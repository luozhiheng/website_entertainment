# Generated by Django 2.0.1 on 2018-03-01 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0015_auto_20180226_0103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='favoritelist',
            name='name',
            field=models.CharField(default='默认列表', max_length=100),
        ),
    ]