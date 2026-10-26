import re
from datetime import datetime, time

from django.conf import settings
from django.contrib.auth import password_validation
from django.utils import timezone
from rest_framework import serializers

from .models import MAIN_PRIZE_RECEIPTS, Product, Receipt, ReceiptPhoto, User


def normalize_phone(value):
    """Приводит российский номер к виду +7XXXXXXXXXX."""
    digits = re.sub(r'\D', '', value or '')
    if len(digits) == 11 and digits[0] in '78':
        return '+7' + digits[1:]
    if len(digits) == 10 and digits[0] == '9':
        return '+7' + digits
    raise serializers.ValidationError('Введите номер в формате +7 (900) 000-00-00')


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, error_messages={'blank': 'Укажите имя'})
    last_name = serializers.CharField(max_length=150, error_messages={'blank': 'Укажите фамилию'})
    email = serializers.EmailField(error_messages={'invalid': 'Проверьте e-mail', 'blank': 'Укажите e-mail'})
    phone = serializers.CharField(max_length=30, error_messages={'blank': 'Укажите телефон'})
    password = serializers.CharField(write_only=True, error_messages={'blank': 'Придумайте пароль'})
    agree_rules = serializers.BooleanField()
    agree_pd = serializers.BooleanField()

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Этот e-mail уже зарегистрирован')
        return value

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate_agree_rules(self, value):
        if not value:
            raise serializers.ValidationError('Нужно согласие с правилами акции')
        return value

    def validate_agree_pd(self, value):
        if not value:
            raise serializers.ValidationError('Нужно согласие на обработку персональных данных')
        return value

    def validate(self, attrs):
        user = User(email=attrs['email'], first_name=attrs['first_name'], last_name=attrs['last_name'])
        try:
            password_validation.validate_password(attrs['password'], user)
        except Exception as exc:  # ValidationError из django
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        now = timezone.now()
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            agreed_rules_at=now,
            agreed_pd_at=now,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages={'invalid': 'Проверьте e-mail', 'blank': 'Укажите e-mail'})
    password = serializers.CharField(error_messages={'blank': 'Введите пароль'})


class ProductSerializer(serializers.ModelSerializer):
    pack_format_display = serializers.CharField(source='get_pack_format_display', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'kind', 'pack_format', 'pack_format_display', 'weight_g', 'sku', 'color']


class ReceiptSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = [
            'id', 'source', 'purchased_at', 'amount', 'fn', 'fd', 'fp', 'status', 'status_display',
            'reject_reason', 'points', 'prize_amount', 'created_at', 'photos',
        ]

    def get_photos(self, obj):
        request = self.context.get('request')
        urls = []
        for photo in obj.photos.all():
            url = photo.image.url
            urls.append(request.build_absolute_uri(url) if request else url)
        return urls


class ReceiptCreateSerializer(serializers.Serializer):
    source = serializers.ChoiceField(choices=Receipt.Source.choices, default=Receipt.Source.MANUAL)
    purchased_at = serializers.DateTimeField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    fn = serializers.CharField(required=False, allow_blank=True)
    fd = serializers.CharField(required=False, allow_blank=True)
    fp = serializers.CharField(required=False, allow_blank=True)
    photos = serializers.ListField(child=serializers.ImageField(), required=False, allow_empty=True)

    def validate_photos(self, photos):
        if len(photos) > settings.RECEIPT_MAX_PHOTOS:
            raise serializers.ValidationError(f'Не более {settings.RECEIPT_MAX_PHOTOS} фото')
        limit = settings.RECEIPT_MAX_PHOTO_MB * 1024 * 1024
        for photo in photos:
            if photo.size > limit:
                raise serializers.ValidationError(f'Файл {photo.name} больше {settings.RECEIPT_MAX_PHOTO_MB} МБ')
        return photos

    def validate(self, attrs):
        errors = {}
        photos = attrs.get('photos') or []

        if attrs['source'] == Receipt.Source.PHOTO:
            if not photos:
                errors['photos'] = 'Добавьте хотя бы одно фото чека'
            if errors:
                raise serializers.ValidationError(errors)
            return attrs

        fn = (attrs.get('fn') or '').strip()
        fd = (attrs.get('fd') or '').strip()
        fp = (attrs.get('fp') or '').strip()
        purchased_at = attrs.get('purchased_at')
        amount = attrs.get('amount')

        if not purchased_at:
            errors['purchased_at'] = 'Укажите дату и время покупки'
        else:
            local_date = timezone.localtime(purchased_at).date()
            if not (settings.PROMO_START <= local_date <= settings.PROMO_END):
                errors['purchased_at'] = (
                    f'Принимаются чеки с {settings.PROMO_START:%d.%m.%Y} по {settings.PROMO_END:%d.%m.%Y}'
                )
            elif purchased_at > timezone.now():
                errors['purchased_at'] = 'Дата покупки не может быть в будущем'
        if amount is None:
            errors['amount'] = 'Укажите сумму чека'
        elif amount <= 0:
            errors['amount'] = 'Сумма должна быть больше нуля'
        if not re.fullmatch(r'\d{16}', fn):
            errors['fn'] = 'ФН — 16 цифр'
        if not re.fullmatch(r'\d{1,10}', fd):
            errors['fd'] = 'ФД — от 1 до 10 цифр'
        if not re.fullmatch(r'\d{8,10}', fp):
            errors['fp'] = 'Проверьте ФП: от 8 до 10 цифр'

        if not errors and Receipt.objects.filter(fn=fn, fd=fd, fp=fp).exists():
            errors['non_field_errors'] = ['Этот чек уже зарегистрирован']

        if errors:
            raise serializers.ValidationError(errors)

        attrs.update(fn=fn, fd=fd, fp=fp)
        return attrs

    def create(self, validated_data):
        photos = validated_data.pop('photos', None) or []
        receipt = Receipt.objects.create(user=self.context['request'].user, **validated_data)
        for photo in photos:
            ReceiptPhoto.objects.create(receipt=receipt, image=photo)
        return receipt


def build_profile(user):
    receipts = list(user.receipts.all())
    accepted = [r for r in receipts if r.status == Receipt.Status.ACCEPTED]
    return {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'is_staff': user.is_staff,
        'stats': {
            'uploaded': len(receipts),
            'accepted': len(accepted),
            'rejected': sum(1 for r in receipts if r.status == Receipt.Status.REJECTED),
            'pending': sum(1 for r in receipts if r.status == Receipt.Status.PENDING),
            'points': sum(r.points for r in accepted),
            'prizes_total': sum(r.prize_amount or 0 for r in accepted),
            'main_prize_progress': min(len(accepted), MAIN_PRIZE_RECEIPTS),
            'main_prize_required': MAIN_PRIZE_RECEIPTS,
        },
        'promo': {
            'start': settings.PROMO_START.isoformat(),
            'end': settings.PROMO_END.isoformat(),
        },
    }


def promo_day_bounds():
    """Начало и конец периода акции как aware datetime (для сидов и тестов)."""
    tz = timezone.get_current_timezone()
    return (
        datetime.combine(settings.PROMO_START, time.min, tzinfo=tz),
        datetime.combine(settings.PROMO_END, time.max, tzinfo=tz),
    )
