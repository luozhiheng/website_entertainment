# Generated by Django 2.0.1 on 2018-02-14 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('music', '0006_album_is_favorite'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='song',
            name='file_type',
        ),
        migrations.AddField(
            model_name='song',
            name='audio_file',
            field=models.FileField(default='', upload_to=''),
        ),
    ]
