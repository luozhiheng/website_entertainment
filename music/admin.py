from django.contrib import admin
from .models import Album,Song,FavoriteList

# Register your models here.
admin.site.register([Album,Song,FavoriteList])