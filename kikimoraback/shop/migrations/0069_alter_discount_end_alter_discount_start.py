# Generated by Django 5.1 on 2025-03-11 09:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0068_alter_discount_end_alter_discount_start"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discount",
            name="end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 3, 11, 9, 14, 25, 390331, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="start",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 3, 11, 9, 14, 25, 390295, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
