from django.conf.urls import url
from . import views
from .forms import UserForm

app_name = 'music'

urlpatterns = [
    url(r'^$', views.index, name='index'),

    # register/
    url(r'register/$', views.register, name='register'),
    # logout/
    url(r'logout/$', views.logout_user, name='logout'),
    # login/
    url(r'login/$', views.login_user, name='login'),

    # /music/1/
    url(r'^(?P<pk>[0-9]+)/$', views.detail, name='detail'),

    # /music/album/add
    url(r'^album/add/$', views.album_create, name='album-add'),
    # /music/album/2/
    url(r'^album/(?P<pk>[0-9]+)/$', views.AlbumUpdate.as_view(), name='album-update'),
    # /music/album/2/delete
    url(r'^album/(?P<pk>[0-9]+)/delete/$', views.AlbumDelete.as_view(), name='album-delete'),
    # /music/album/2/update
    url(r'^album/(?P<pk>[0-9]+)/update/$', views.AlbumUpdate.as_view(), name='album-update'),
    # /music/2/favorite/
    url(r'^(?P<pk>[0-9]+)/favorite/$', views.album_favorite, name='album-favorite'),

    # /music/2/song_create/
    url(r'^(?P<pk>[0-9]+)/song-create/$', views.song_create, name='song-create'),
    # /music/2/song-delete/3/
    url(r'^(?P<pk>[0-9]+)/song-delete/(?P<song_id>[0-9]+)/$', views.song_delete, name='song-delete'),
    # /music/2/song-favorite/3/
    url(r'^(?P<song_id>[0-9]+)/song-favorite/$', views.song_favorite, name='favorite'),

    # /music/songs/filter_by/
    url(r'^songs/(?P<filter_by>[a-zA-Z]+)/$', views.songs, name='songs'),
    # /music/albums/filter_by/
    url(r'^albums/(?P<filter_by>[a-zA-Z]+)/$', views.albums, name='albums'),

]
