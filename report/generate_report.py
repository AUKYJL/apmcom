#!/usr/bin/env python3
"""Отчёт за 01.12–27.12.2026 из PostgreSQL; исходный шаблон не изменяется."""
import re
import sys
import tempfile
from copy import copy
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl
import psycopg
from openpyxl.styles import Alignment
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'
TEMPLATE = REPORT / 'Шаблон отчёта — Лесная Чашка.xlsx'
OUTPUT = REPORT / 'Лесная Чашка — отчёт недели 1-4.xlsx'
TZ = ZoneInfo('Europe/Moscow')
START = datetime(2026, 12, 1, tzinfo=TZ)
END = datetime(2026, 12, 28, tzinfo=TZ)  # Конечная граница не включается.
WEEK_STARTS = [date(2026, 12, d) for d in (1, 7, 14, 21)]
WEEK_ENDS = [date(2026, 12, d) for d in (7, 14, 21, 28)]
EXCLUDED_CODES = (
    '20261201000000000004',
    '20261201000000000016',
    '20261201000000000032',
    '20261201000000000101',
    '20261201000000000125',
    '20261201000000000215',
)
FIELDS = ('registrations', 'participants', 'new_participants', 'previous_promo',
          'uploaded', 'accepted', 'packs')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def connect_database():
    sys.path.insert(0, str(ROOT / 'backend'))
    from config.settings import DATABASES
    db = DATABASES['default']
    return psycopg.connect(dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'],
                         host=db['HOST'], port=db['PORT'], connect_timeout=10,
                         row_factory=dict_row)


def fetch_data():
    parts = re.split(r'^-- name: (\w+)\n', (REPORT / 'queries.sql').read_text(), flags=re.M)
    queries = dict(zip(parts[1::2], parts[2::2]))
    params = dict(excluded_codes=list(EXCLUDED_CODES), timezone=TZ.key, start=START, end=END,
                  week_numbers=[1, 2, 3, 4], week_starts=WEEK_STARTS, week_ends=WEEK_ENDS)
    with connect_database() as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        conn.execute("SET LOCAL TIME ZONE 'Europe/Moscow'")
        conn.execute("SET LOCAL statement_timeout = '30s'")
        return {name: conn.execute(queries['base'] + query, params).fetchall()
                for name, query in queries.items() if name != 'base'}


def verify_data(data):
    """Проверить качество исходных данных и баланс уже рассчитанных SQL-агрегатов."""
    errors = [name for name, count in data['quality'][0].items() if count]
    require(not errors, 'Ошибка качества данных: ' + ', '.join(errors))
    weekly, total = data['weekly'], data['totals'][0]
    require([w['week'] for w in weekly] == [1, 2, 3, 4], 'Ожидались четыре недели.')
    for w in weekly:
        require(w['uploaded'] == w['accepted'] + w['rejected'] + w['pending'],
                'Не сошёлся баланс статусов чеков.')
        require(w['previous_promo'] <= w['new_participants'] <= w['participants'],
                'Нарушено соотношение новых и уникальных участников.')
    for key in ('registrations', 'uploaded', 'accepted', 'rejected', 'pending', 'packs'):
        require(sum(w[key] for w in weekly) == total[key], f'Не сошёлся итог: {key}.')
    require(len(data['daily']) == 27, 'Ожидались 27 дней.')
    for w, lo, hi in zip(weekly, WEEK_STARTS, WEEK_ENDS):
        for key in ('registrations', 'accepted'):
            require(sum(d[key] for d in data['daily'] if lo <= d['day'] < hi) == w[key],
                    f'Дневные и недельные показатели не совпадают: {key}.')
        require(sum(r['count'] for r in data['reasons'] if r['week'] == w['week']) == w['rejected'],
                'Не сошлась сумма причин отклонения.')
    require(sum(s['quantity'] for s in data['sku']) == total['packs'], 'Не сошлась сумма SKU.')
    require(len(data['participants']) == total['participants'], 'Не сошлось число участников.')
    for key in ('uploaded', 'accepted', 'points', 'prizes'):
        require(sum(p[key] for p in data['participants']) == total[key],
                f'Не сошёлся итог по участникам: {key}.')


def fill_workbook(template, data):
    book = openpyxl.load_workbook(template)
    changes = {s.title: set() for s in book}

    def put(sheet, row, col, value):
        cell = book[sheet].cell(row, col, value)
        changes[sheet].add(cell.coordinate)
        return cell

    for week in data['weekly']:
        row = week['week'] + 8
        for col, field in zip((4, 5, 6, 8, 10, 11, 12), FIELDS):
            put('Тотал', row, col, week[field])
    daily_rows = {r[0].value.date(): r[0].row for r in book['Динамика ежедневная'] if isinstance(r[0].value, datetime)}
    for day in data['daily']:
        require(day['day'] in daily_rows, 'Дата не соответствует датам в шаблоне.')
        row = daily_rows[day['day']]
        for col, key in ((3, 'registrations'), (4, 'accepted')):
            put('Динамика ежедневная', row, col, day[key])
    reason_sheet = book['Причины отклонения чеков']
    headers = {reason_sheet.cell(3, c).value: c for c in range(4, 14)}
    require(len(headers) == 10 and None not in headers, 'Заголовки причин отклонения неоднозначны.')
    counts = {(r['week'], r['reject_reason']): r['count'] for r in data['reasons']}
    require(all(reason in headers for _, reason in counts), 'Неизвестная причина отклонения; невозможно сопоставить её с шаблоном.')
    for week in range(1, 5):
        for reason, col in headers.items():
            put(reason_sheet.title, week + 3, col, counts.get((week, reason), 0))
    sku = {r['pack_format']: r['quantity'] for r in data['sku']}
    require(set(sku) <= {'bags20', 'bags100', 'loose75'}, 'Неизвестный формат SKU; необходимо обновить шаблон.')
    for row, key in enumerate(('bags20', 'bags100', 'loose75'), 3):
        put('SKU', row, 2, sku.get(key, 0))
    require(len(data['participants']) <= 1048573, 'Число участников превышает допустимое число строк Excel.')
    for row, p in enumerate(data['participants'], 4):
        values = (p['participant_code'], p['registration_day'], p['uploaded'], p['accepted'],
                  p['points'], p['prizes'], 'Да' if p['previous_promo'] else 'Нет')
        for col, value in enumerate(values, 1):
            cell = put('Участники', row, col, value)
            cell._style = copy(book['Динамика ежедневная']['C5']._style)
            cell.number_format = '@' if col == 1 else 'dd.mm.yyyy' if col == 2 else '#,##0'
            if col in (1, 7):
                cell.alignment = Alignment(horizontal='left', vertical='center')
        book['Участники'].row_dimensions[row].height = 20
    return book, changes


def verify_workbook(template, output, expected, changes):
    """Проверить записанные данные, исходные формулы, план и оформление."""
    original = openpyxl.load_workbook(template)
    actual = openpyxl.load_workbook(output)
    require(len(actual.sheetnames) == 5 and actual.sheetnames == original.sheetnames,
            'Изменилась структура пяти листов.')
    for old, new, wanted in zip(original, actual, expected):
        require(str(old.merged_cells) == str(new.merged_cells), 'Изменились объединения ячеек.')
        require({k: dict(v) for k, v in old.column_dimensions.items()} ==
                {k: dict(v) for k, v in new.column_dimensions.items()},
                'Изменилась ширина столбцов.')
        require(old.freeze_panes == new.freeze_panes, 'Изменились закреплённые области.')
        require(len(old._charts) == len(new._charts), 'Не сохранена диаграмма.')
        for row in old:
            for cell in row:
                other = new[cell.coordinate]
                require(cell._style == other._style,
                        f'Изменился стиль: {old.title}!{cell.coordinate}.')
                if cell.data_type == 'f' or cell.coordinate not in changes[old.title]:
                    require(cell.value == other.value,
                            f'Изменилась исходная ячейка: {old.title}!{cell.coordinate}.')
        for address in changes[new.title]:
            value, target = new[address].value, wanted[address].value
            if isinstance(target, date) and not isinstance(target, datetime):
                value = value.date() if isinstance(value, datetime) else value
            require(value == target, f'Не записаны данные: {new.title}!{address}.')
    original.close()
    actual.close()


def main():
    data = fetch_data()
    verify_data(data)
    book, changes = fill_workbook(TEMPLATE, data)
    # Проверяем временный файл до замены готового отчёта.
    with tempfile.NamedTemporaryFile(dir=REPORT, suffix='.xlsx', delete=False) as temp:
        pending = Path(temp.name)
    try:
        book.save(pending)
        verify_workbook(TEMPLATE, pending, book, changes)
        pending.replace(OUTPUT)
    finally:
        pending.unlink(missing_ok=True)
    print('Отчёт проверен: пять листов, данные, исходные формулы, план и оформление.')
    print('Итоги:', data['totals'][0])
    print(f'Уникальных участников за 4 недели: {data["totals"][0]["participants"]}')
    print('Формулы пересчитает Excel при открытии; ошибки исходных формул не исправляются.')
    print(OUTPUT)


if __name__ == '__main__':
    try:
        main()
    except psycopg.Error as exc:
        sys.exit(f'Отчёт не сформирован: ошибка PostgreSQL {type(exc).__name__}; '
                 'проверьте backend/.env и доступность базы данных.')
    except (ValueError, OSError) as exc:
        sys.exit(f'Отчёт не сформирован: {exc}')
