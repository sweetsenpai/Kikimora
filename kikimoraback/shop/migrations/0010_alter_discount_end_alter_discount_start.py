# Generated by Django 5.1 on 2025-02-18 13:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0009_alter_discount_end_alter_discount_start"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discount",
            name="end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 18, 13, 0, 37, 70907, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="start",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 18, 13, 0, 37, 70894, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
