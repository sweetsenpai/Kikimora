# Generated by Django 5.1 on 2025-03-10 14:10

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0058_product_available_alter_discount_end_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discount",
            name="end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 3, 10, 14, 9, 59, 330029, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="start",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 3, 10, 14, 9, 59, 330010, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
