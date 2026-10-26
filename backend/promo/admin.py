import csv

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html

from .models import Product, Receipt, ReceiptPhoto, User


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'pack_format', 'weight_g', 'sku', 'price', 'sort_order', 'is_active']
    list_editable = ['sort_order', 'is_active']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    list_display = ['email', 'participant_code', 'first_name', 'last_name', 'phone', 'date_joined', 'is_staff']
    search_fields = ['email', 'participant_code', 'first_name', 'last_name', 'phone']
    fieldsets = (
        (None, {'fields': ('email', 'participant_code', 'password')}),
        ('Данные участника', {'fields': ('first_name', 'last_name', 'phone', 'agreed_rules_at', 'agreed_pd_at')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),
    )


class ReceiptPhotoInline(admin.TabularInline):
    model = ReceiptPhoto
    extra = 0
    readonly_fields = ['preview', 'uploaded_at']
    fields = ['preview', 'image', 'uploaded_at']

    @admin.display(description='превью')
    def preview(self, obj):
        if not obj.image:
            return '—'
        return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height:160px"></a>', obj.image.url)


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'source', 'purchased_at', 'amount', 'fd', 'status', 'points', 'prize_amount', 'created_at']
    list_filter = ['status', 'source', 'created_at']
    search_fields = ['fn', 'fd', 'fp', 'user__email', 'user__phone']
    readonly_fields = ['created_at', 'reviewed_at']
    inlines = [ReceiptPhotoInline]
    actions = ['accept_receipts', 'reject_receipts', 'export_csv']
    list_select_related = ['user']

    @admin.action(description='Принять выбранные чеки')
    def accept_receipts(self, request, queryset):
        count = 0
        for receipt in queryset.exclude(status=Receipt.Status.ACCEPTED):
            receipt.accept()
            count += 1
        self.message_user(request, f'Принято чеков: {count}')

    @admin.action(description='Отклонить выбранные чеки')
    def reject_receipts(self, request, queryset):
        count = 0
        for receipt in queryset.exclude(status=Receipt.Status.REJECTED):
            receipt.reject('Чек не прошёл проверку фискальных данных')
            count += 1
        self.message_user(request, f'Отклонено чеков: {count}')

    @admin.action(description='Выгрузить в CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="receipts_{timezone.localdate():%Y%m%d}.csv"'
        response.write('﻿')  # BOM, чтобы Excel открыл кириллицу
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['id', 'email', 'телефон', 'способ', 'дата покупки', 'сумма', 'ФН', 'ФД', 'ФП',
                         'статус', 'баллы', 'приз, ₽', 'загружен'])
        for r in queryset.select_related('user'):
            writer.writerow([
                r.id, r.user.email, r.user.phone, r.get_source_display(),
                timezone.localtime(r.purchased_at).strftime('%d.%m.%Y %H:%M') if r.purchased_at else '',
                str(r.amount).replace('.', ',') if r.amount is not None else '',
                r.fn, r.fd, r.fp, r.get_status_display(), r.points, r.prize_amount or '',
                timezone.localtime(r.created_at).strftime('%d.%m.%Y %H:%M'),
            ])
        return response
