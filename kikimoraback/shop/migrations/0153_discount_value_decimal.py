# Generated by Django 5.1.8 on 2025-05-29 15:01

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0152_alter_product_price_alter_product_weight"),
    ]

    operations = [
        migrations.AddField(
            model_name="discount",
            name="value_decimal",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                help_text="Процент скидки или сумма скидки",
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
            ),
        ),
    ]
