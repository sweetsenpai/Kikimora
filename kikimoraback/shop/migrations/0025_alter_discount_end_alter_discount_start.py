# Generated by Django 5.1 on 2025-02-20 13:57

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0024_alter_discount_end_alter_discount_start"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discount",
            name="end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 20, 13, 57, 23, 286839, tzinfo=datetime.timezone.utc
                )
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="start",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 2, 20, 13, 57, 23, 286825, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
