from decimal import Decimal

from rest_framework.test import APITestCase

from .models import Product


class ProductApiTests(APITestCase):
    def test_only_active_products_in_order(self):
        Product.objects.create(name='Б', pack_format='bags20', weight_g=30, sku='B', price=Decimal('1'), sort_order=2)
        Product.objects.create(name='А', pack_format='bags100', weight_g=150, sku='A', price=Decimal('1'), sort_order=1)
        Product.objects.create(name='Скрыт', pack_format='loose75', weight_g=75, sku='C', price=Decimal('1'), is_active=False)
        data = self.client.get('/api/products/').json()
        self.assertEqual([p['name'] for p in data], ['А', 'Б'])
        self.assertEqual(data[0]['pack_format_display'], '100 пакетиков')
