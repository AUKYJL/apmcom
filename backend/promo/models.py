import random
from decimal import Decimal

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q
from django.utils import timezone

# Гарантированные призы на телефон, ₽.
GUARANTEED_PRIZES = [50, 70, 100, 150, 200, 300]
# Чек дороже этой суммы приносит 2 балла вместо 1.
DOUBLE_POINTS_THRESHOLD = Decimal('1000')
# Сколько принятых чеков нужно для участия в розыгрыше главного приза.
MAIN_PRIZE_RECEIPTS = 3
# Причины отклонения чека (как в еженедельном отчёте).
REJECT_REASONS = [
    'Чек уже зарегистрирован',
    'Нет фото чека',
    'Магазин не участвует в акции',
    'В чеке нет акционного продукта',
    'Недостаточная итоговая сумма по акционным товарам в чеке',
    'Чек не прошёл проверку фискальных данных',
    'Чек сфотографирован неполностью',
    'Чек плохого качества',
    'На фото более одного чека',
    'Дата покупки в чеке не соответствует правилам',
]


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError('Нужен e-mail')
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault('is_staff', False)
        extra.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Участник акции. Входит по e-mail, имени пользователя нет."""

    username = None
    email = models.EmailField('e-mail', unique=True)
    participant_code = models.CharField('ID участника', max_length=20, unique=True, null=True, blank=True,
                                        help_text='Сквозной идентификатор участника в CRM агентства')
    phone = models.CharField('телефон', max_length=20, blank=True)
    agreed_rules_at = models.DateTimeField('согласие с правилами', null=True, blank=True)
    agreed_pd_at = models.DateTimeField('согласие на обработку ПД', null=True, blank=True)
    # Маркетинговые поля: заполняются при регистрации, используются в отчётах.
    utm_source = models.CharField('utm_source', max_length=100, blank=True)
    utm_campaign = models.CharField('utm_campaign', max_length=100, blank=True)
    prev_promo_participant = models.BooleanField('участвовал в прошлой акции', default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'участник'
        verbose_name_plural = 'участники'

    def __str__(self):
        return self.email


class Product(models.Model):
    """Акционная продукция."""

    class PackFormat(models.TextChoices):
        BAGS_20 = 'bags20', '20 пакетиков'
        BAGS_100 = 'bags100', '100 пакетиков'
        LOOSE_75 = 'loose75', 'Листовой 75 г'

    name = models.CharField('название', max_length=100)
    kind = models.CharField('вид', max_length=50, default='травяной чай')
    pack_format = models.CharField('формат', max_length=10, choices=PackFormat.choices)
    weight_g = models.PositiveIntegerField('вес, г')
    sku = models.CharField('артикул', max_length=20, unique=True)
    color = models.CharField('цвет пачки', max_length=7, default='#B5473A')
    price = models.DecimalField('цена, ₽', max_digits=8, decimal_places=2)
    sort_order = models.PositiveSmallIntegerField('порядок', default=0)
    is_active = models.BooleanField('показывать на сайте', default=True)

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'акционная продукция'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.name}, {self.get_pack_format_display()}'


class Receipt(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'На проверке'
        ACCEPTED = 'accepted', 'Принят'
        REJECTED = 'rejected', 'Отклонён'

    class Source(models.TextChoices):
        MANUAL = 'manual', 'Ввод вручную'
        PHOTO = 'photo', 'Фото чека'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts', verbose_name='участник')
    source = models.CharField('способ загрузки', max_length=10, choices=Source.choices, default=Source.MANUAL)
    purchased_at = models.DateTimeField('дата и время покупки', null=True, blank=True)
    amount = models.DecimalField('сумма, ₽', max_digits=10, decimal_places=2, null=True, blank=True)
    fn = models.CharField('ФН', max_length=16, blank=True)
    fd = models.CharField('ФД', max_length=10, blank=True)
    fp = models.CharField('ФП', max_length=10, blank=True)
    status = models.CharField('статус', max_length=10, choices=Status.choices, default=Status.PENDING)
    reject_reason = models.CharField('причина отклонения', max_length=255, blank=True)
    points = models.PositiveSmallIntegerField('баллы', default=0)
    prize_amount = models.PositiveIntegerField('приз на телефон, ₽', null=True, blank=True)
    created_at = models.DateTimeField('загружен', auto_now_add=True)
    reviewed_at = models.DateTimeField('проверен', null=True, blank=True)

    class Meta:
        verbose_name = 'чек'
        verbose_name_plural = 'чеки'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['fn', 'fd', 'fp'],
                condition=~Q(fn=''),
                name='unique_receipt_fiscal_data',
            ),
        ]

    def __str__(self):
        return f'Чек {self.fd or self.pk} ({self.get_status_display()})'

    def calculate_points(self):
        if self.amount is not None and self.amount > DOUBLE_POINTS_THRESHOLD:
            return 2
        return 1

    def accept(self):
        self.status = self.Status.ACCEPTED
        self.reject_reason = ''
        self.points = self.calculate_points()
        if self.prize_amount is None:
            self.prize_amount = random.choice(GUARANTEED_PRIZES)
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reason):
        self.status = self.Status.REJECTED
        self.reject_reason = reason
        self.points = 0
        self.prize_amount = None
        self.reviewed_at = timezone.now()
        self.save()


class ReceiptItem(models.Model):
    """Акционные позиции в чеке — заполняет модератор при проверке (или распознавание чека)."""

    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='items', verbose_name='чек')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='receipt_items', verbose_name='продукт')
    quantity = models.PositiveSmallIntegerField('количество, шт', default=1)

    class Meta:
        verbose_name = 'позиция чека'
        verbose_name_plural = 'позиции чеков'


class ReceiptPhoto(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='photos', verbose_name='чек')
    image = models.ImageField('фото', upload_to='receipts/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'фото чека'
        verbose_name_plural = 'фото чеков'

    def __str__(self):
        return self.image.name
