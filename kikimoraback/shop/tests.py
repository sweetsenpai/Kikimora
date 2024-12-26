from django.test import TestCase
from .forms import DiscountForm
from .models import Category, Subcategory, Product, Discount


class DiscountFormTest(TestCase):

    def setUp(self):
        # Создаем тестовые данные
        self.category = Category.objects.create(name="Category 1")
        self.subcategory = Subcategory.objects.create(name="Subcategory 1", category=self.category)
        self.product = Product.objects.create(name="Product 1", subcategory=self.subcategory, photo_url='1111')

    def test_form_valid_with_product(self):
        # Тестируем форму, когда указан продукт
        form_data = {
            'discount_type': 'percentage',
            'value': 20,
            'description': 'Test discount',
            'start': '2024-01-01 00:00:00',
            'end': '2024-12-31 23:59:59',
            'product': self.product.product_id
        }
        form = DiscountForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что категория и подкатегория обнулены
        cleaned_data = form.clean()
        self.assertIsNone(cleaned_data.get('category'))
        self.assertIsNone(cleaned_data.get('subcategory'))

    def test_form_valid_with_subcategory(self):
        # Тестируем форму, когда указана подкатегория и продукт не указан
        form_data = {
            'discount_type': 'percentage',
            'value': 20,
            'description': 'Test discount',
            'start': '2024-01-01 00:00:00',
            'end': '2024-12-31 23:59:59',
            'subcategory': self.subcategory.subcategory_id
        }
        form = DiscountForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что категория обнулена
        cleaned_data = form.clean()
        self.assertIsNone(cleaned_data.get('category'))

    def test_form_invalid_with_percentage_over_100(self):
        # Тестируем форму, когда процентная скидка больше 100
        form_data = {
            'discount_type': 'percentage',
            'value': 120,
            'description': 'Test discount',
            'start': '2024-01-01 00:00:00',
            'end': '2024-12-31 23:59:59'
        }
        form = DiscountForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('value', form.errors)
        self.assertEqual(form.errors['value'][0], 'Процент скидки не может быть больше 100!')

    def test_form_valid_with_fixed_discount(self):
        # Тестируем форму с фиксированной скидкой
        form_data = {
            'discount_type': 'amount',
            'value': 50,
            'description': 'Fixed amount discount',
            'start': '2024-01-01 00:00:00',
            'end': '2024-12-31 23:59:59'
        }
        form = DiscountForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_value(self):
        # Тестируем форму без значения скидки
        form_data = {
            'discount_type': 'percentage',
            'description': 'Discount without value',
            'start': '2024-01-01 00:00:00',
            'end': '2024-12-31 23:59:59'
        }
        form = DiscountForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('value', form.errors)

