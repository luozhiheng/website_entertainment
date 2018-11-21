from django import forms
from django.contrib.auth.models import User
from .models import Album, Song


class AlbumForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(AlbumForm, self).__init__(*args, **kwargs)
        self.fields['artist'] = forms.CharField(
            required=True,
            label="艺人",
            help_text="不能为空",
            error_messages={'required': "以下是必填项"},
        )
        self.fields['album_title'] = forms.CharField(
            required=True,
            label="专辑名",
            help_text="不能为空",
            error_messages={'required': "以下是必填项"},
        )
        self.fields['genre'] = forms.Field(
            required=False,
            label="描述",
            widget=forms.Textarea
        )
        self.fields['album_logo'] = forms.FileField(
            required=False,
            label="封面图片",
        )
        self.fields['album_backpic'] = forms.FileField(
            required=False,
            label="背面图片",
        )

    class Meta:
        model = Album
        fields = ['artist', 'album_title', 'genre', 'album_logo', 'album_backpic']


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['song_title', 'audio_file']


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
