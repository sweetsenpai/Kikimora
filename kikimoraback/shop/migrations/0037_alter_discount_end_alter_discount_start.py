# Generated by Django 5.1 on 2025-02-28 09:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0036_alter_discount_end_alter_discount_start"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discount",
            name="end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 28, 9, 24, 45, 393438, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="start",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 28, 9, 24, 45, 393424, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
