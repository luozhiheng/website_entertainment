# Generated by Django 2.0.1 on 2018-02-22 03:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0009_auto_20180221_2139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='album_logo',
            field=models.FileField(blank=True, default='', null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='song',
            name='audio_file',
            field=models.FileField(blank=True, default='', null=True, upload_to=''),
        ),
    ]
