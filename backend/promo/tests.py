import shutil
import tempfile
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from .models import Receipt, User

PERIOD = {'PROMO_START': datetime(2026, 1, 1).date(), 'PROMO_END': datetime(2026, 12, 31).date()}


def make_image(name='check.png'):
    buf = BytesIO()
    Image.new('RGB', (10, 10), 'white').save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


class AuthTests(APITestCase):
    def payload(self, **overrides):
        data = {
            'first_name': 'Мария', 'last_name': 'Иванова', 'email': 'Maria@Example.com',
            'phone': '8 (900) 123-45-67', 'password': 'Very-strong-123',
            'agree_rules': True, 'agree_pd': True,
        }
        data.update(overrides)
        return data

    def test_register_logs_in_and_normalizes_fields(self):
        res = self.client.post('/api/auth/register/', self.payload(), format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['email'], 'maria@example.com')
        self.assertEqual(res.data['phone'], '+79001234567')
        self.assertEqual(self.client.get('/api/me/').status_code, 200)

    def test_register_requires_both_consents(self):
        res = self.client.post('/api/auth/register/', self.payload(agree_pd=False), format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('agree_pd', res.data)

    def test_duplicate_email_is_rejected(self):
        self.client.post('/api/auth/register/', self.payload(), format='json')
        self.client.post('/api/auth/logout/')
        res = self.client.post('/api/auth/register/', self.payload(email='maria@example.com'), format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('email', res.data)

    def test_login_with_wrong_password(self):
        User.objects.create_user('a@example.com', 'Right-pass-123')
        res = self.client.post('/api/auth/login/', {'email': 'a@example.com', 'password': 'nope'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get('/api/me/').status_code, 403)


TEST_MEDIA = tempfile.mkdtemp(prefix='promo-test-media-')


@override_settings(MEDIA_ROOT=TEST_MEDIA, **PERIOD)
class ReceiptTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user('u@example.com', 'Right-pass-123')
        self.client.force_authenticate(self.user)

    def manual(self, **overrides):
        data = {
            'source': 'manual', 'purchased_at': '2026-03-12T18:40:00+03:00', 'amount': '1248.90',
            'fn': '9960440300123456', 'fd': '48213', 'fp': '1234567890',
        }
        data.update(overrides)
        return data

    def test_manual_receipt_is_created_pending(self):
        res = self.client.post('/api/receipts/', self.manual())
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['status'], 'pending')

    def test_fiscal_fields_are_validated(self):
        res = self.client.post('/api/receipts/', self.manual(fn='123', fp='12345'))
        self.assertEqual(res.status_code, 400)
        self.assertIn('fn', res.data)
        self.assertIn('fp', res.data)

    def test_date_outside_promo_period_is_rejected(self):
        res = self.client.post('/api/receipts/', self.manual(purchased_at='2025-12-31T12:00:00+03:00'))
        self.assertEqual(res.status_code, 400)
        self.assertIn('purchased_at', res.data)

    def test_duplicate_receipt_is_rejected(self):
        self.client.post('/api/receipts/', self.manual())
        res = self.client.post('/api/receipts/', self.manual())
        self.assertEqual(res.status_code, 400)

    def test_photo_receipt_requires_photo(self):
        res = self.client.post('/api/receipts/', {'source': 'photo'})
        self.assertEqual(res.status_code, 400)
        res = self.client.post('/api/receipts/', {'source': 'photo', 'photos': [make_image(), make_image('b.png')]})
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(len(res.data['photos']), 2)

    def test_points_on_accept(self):
        big = Receipt.objects.create(user=self.user, amount=Decimal('1000.01'), fn='1' * 16, fd='1', fp='12345678')
        small = Receipt.objects.create(user=self.user, amount=Decimal('1000.00'), fn='2' * 16, fd='2', fp='12345678')
        big.accept()
        small.accept()
        self.assertEqual(big.points, 2)
        self.assertEqual(small.points, 1)
        stats = self.client.get('/api/me/').data['stats']
        self.assertEqual(stats['points'], 3)
        self.assertEqual(stats['accepted'], 2)
        self.assertEqual(stats['prizes_total'], big.prize_amount + small.prize_amount)

    def test_user_sees_only_own_receipts(self):
        other = User.objects.create_user('o@example.com', 'Right-pass-123')
        Receipt.objects.create(user=other, fn='3' * 16, fd='3', fp='12345678', purchased_at=timezone.now())
        res = self.client.get('/api/receipts/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 0)
