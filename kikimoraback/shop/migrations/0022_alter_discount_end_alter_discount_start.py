# Generated by Django 5.1 on 2025-02-19 15:51

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0021_alter_discount_end_alter_discount_start"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discount",
            name="end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 19, 15, 51, 4, 354083, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="start",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 19, 15, 51, 4, 354069, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
