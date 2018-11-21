from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
import re


# Create your models here.
class Album(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artist = models.CharField(max_length=100)
    album_title = models.CharField(max_length=100)
    genre = models.TextField(max_length=2000, blank=True, null=True)
    album_logo = models.FileField(null=True, blank=True)
    album_backpic = models.FileField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('music:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.artist + '-' + self.album_title + '- user:' + self.user.username


class Song(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    song_title = models.CharField(max_length=100)
    audio_file = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.album.artist + '-' + self.song_title + '-专辑:' + '《' + self.album.album_title + '》'


class FavoriteList(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default='默认列表')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite')
    songs_favorite = models.ManyToManyField(Song, related_name='+', blank=True)
    albums_favorite = models.ManyToManyField(Album, related_name='+', blank=True)

    def __str__(self):
        return '{0}_{1}_{2}'.format(self.user, self.name, self.id)
