# Generated by Django 3.2.19 on 2023-08-13 13:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_alter_cart_model_to_subscribe'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tag',
            options={'ordering': ['-id'], 'verbose_name': 'Тэг', 'verbose_name_plural': 'Тэги'},
        ),
    ]
