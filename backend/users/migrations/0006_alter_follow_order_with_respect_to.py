# Generated by Django 3.2.19 on 2023-08-10 20:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20230726_2101'),
    ]

    operations = [
        migrations.AlterOrderWithRespectTo(
            name='follow',
            order_with_respect_to='author',
        ),
    ]