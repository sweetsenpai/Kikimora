# Generated by Django 5.1.8 on 2025-05-30 13:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0158_remove_promosystem_amount_decimal_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="promosystem",
            name="usage_count",
        ),
    ]
