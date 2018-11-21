from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import logout, authenticate, login
from .forms import UserForm, AlbumForm
import os
from music.models import Album, Song, FavoriteList
from .forms import SongForm
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
import uuid
from PIL import Image
from celery_app.tasks import img2text_ocr

# from django.db import connection
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_FILE_TYPES = ['wav', 'mp3', 'ogg']
IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']
init_list_name = '默认列表'


def index(request):
    if not request.user.is_authenticated:
        return render(request, 'music/login.html')
    else:
        albums_q = Album.objects.filter(user=request.user)
        query = request.GET.get('q')
        favorite_list = request.user.favorite.filter(name=init_list_name)
        if len(favorite_list) == 0:
            favorite_list = FavoriteList(name=init_list_name, user=request.user)
            favorite_list.save()
            favorite_list = request.user.favorite.filter(name=init_list_name).get()  # len() 执行了query，重新获取
        else:
            favorite_list = favorite_list.get()
        id_albums_favorite = [al.id for al in favorite_list.albums_favorite.all()]
        id_songs_favorite = [song.id for song in favorite_list.songs_favorite.all()]
        if query:
            search = 1
            albums_q = albums_q.filter(
                Q(album_title__contains=query) | Q(artist__contains=query)
            )
            song_result = Song.objects.filter(
                Q(song_title__contains=query) | Q(album__album_title__contains=query)
            )
            return render(request, 'music/index.html',
                          {'albums': albums_q.order_by('id'), 'songs': song_result.order_by('id'),
                           'id_albums_favorite': id_albums_favorite,
                           'id_songs_favorite': id_songs_favorite,
                           'search': search})
        else:
            # print(connection.queries)
            search = ''
            return render(request, 'music/index.html',
                          {'albums': albums_q.order_by('id'), 'id_albums_favorite': id_albums_favorite,
                           'search': search})


def detail(request, pk):
    if not request.user.is_authenticated:
        return render(request, 'music/login.html')
    else:
        belong = 'N'
        album = get_object_or_404(Album, pk=pk)
        if album.user.id == request.user.id:
            belong = 'Y'
        favorite_list = request.user.favorite.get(name=init_list_name)
        id_songs_favorite = [song.id for song in favorite_list.songs_favorite.all()]
        all_songs = [song for song in album.song_set.all()]
        return render(request, 'music/detail.html',
                      {'album': album, 'id_songs_favorite': id_songs_favorite, 'belong': belong,
                       'all_songs': all_songs})


def album_create(request):
    if not request.user.is_authenticated:
        return render(request, 'music/login.html')
    else:
        form = AlbumForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            if request.user.album_set.filter(Q(album_title=album.album_title) & Q(artist=album.artist)):
                context = {
                    'form': form,
                    'error_message': "你已经创建了相同的专辑"
                }
                return render(request, 'music/album_form_add.html', context)

            if 'album_logo' in request.FILES.keys():  # 上传了logo文件
                file = request.FILES['album_logo']
                file_path = deal_file(file, 'pic', request.user.id)
                if file_path == "fail":
                    context = {
                        'form': form,
                        'error_message': "文件格式应为png, jpg, jpeg"
                    }
                    return render(request, 'music/album_form_add.html', context)
                else:
                    album.album_logo = file_path
            else:  # 没上传logo，则字段置空
                album.album_logo = ''
            if request.POST.get('intelligent') == 'Y':  # 智能创建
                pass
            album.save()
            return render(request, 'music/detail.html', {'album': album})
        else:
            return render(request, 'music/album_form_add.html', {'form': form})


class AlbumUpdate(UpdateView):
    model = Album
    form_class = AlbumForm
    template_name_suffix = '_update_form'
    permission_required = ''
    permission_fail_message = ('无权进行此操作')

    def get_form_kwargs(self):  # override parent method
        kwargs = super(AlbumUpdate, self).get_form_kwargs()
        kwargs.update({
            'user': self.request.user
        })
        return kwargs


class AlbumDelete(DeleteView):
    model = Album
    success_url = reverse_lazy('music:index')
    permission_required = ''
    permission_fail_message = ('无权进行此操作')


def song_create(request, pk):
    form = SongForm(request.POST or None, request.FILES or None)
    album = get_object_or_404(Album, pk=pk)
    if form.is_valid():
        album_songs = album.song_set.all()
        for s in album_songs:
            if s.song_title == form.cleaned_data.get('song_title'):
                context = {
                    'album': album,
                    'form': form,
                    'error_message': '已添加相同的歌曲'
                }
                return render(request, 'music/create_song.html', context=context)
        song = form.save(commit=False)
        song.album = album
        song.audio_file = request.FILES['audio_file']
        file_type = song.audio_file.url.split('.')[-1]
        file_type = file_type.lower()
        if file_type not in AUDIO_FILE_TYPES:
            context = {
                'album': album,
                'form': form,
                'error_message': '文件的格式为：wav,mp3,ogg'
            }
            render(request, 'music/create_song.html', context=context)
        song.save()
        return redirect(album)
    context = {
        'album': album,
        'form': form,
    }
    return render(request, 'music/create_song.html', context=context)


def song_delete(request, pk, song_id):
    album = get_object_or_404(Album, pk=pk)
    song = Song.objects.get(pk=song_id)
    if album.user.username == request.user.username:
        if song.audio_file:
            os.remove(song.audio_file.path)
        song.delete()
        return redirect('music:detail', pk=pk)
    else:
        return render(request, 'music/detail.html', {'error_message': '你无权删除他人的歌曲', 'album': album})


def album_favorite(request, pk):  # TODO 后续若要增加创建喜爱列表的功能，则此处要修改，目前按设计这个功能不大必要
    try:
        album = get_object_or_404(Album, pk=pk)
        favorite_list = request.user.favorite.filter(name=init_list_name)
        if len(favorite_list) == 0:
            favorite_list = FavoriteList(name=init_list_name, user=request.user)
            favorite_list.save()
            favorite_list = request.user.favorite.filter(name=init_list_name)
        favorite_list = favorite_list.get()
        find = favorite_list.albums_favorite.filter(pk=album.id).count()
        if find == 1:
            favorite_list.albums_favorite.remove(album)
        else:
            favorite_list.albums_favorite.add(album)
        favorite_list.save()
    except(KeyError, Album.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True, 'albumidlist': ([al.id for al in favorite_list.albums_favorite.all()])})


def song_favorite(request, song_id):
    try:
        song = get_object_or_404(Song, pk=song_id)
        favorite_list = request.user.favorite.filter(name=init_list_name)
        if len(favorite_list) == 0:
            favorite_list = FavoriteList(name=init_list_name, user=request.user)
            favorite_list.save()
            favorite_list = request.user.favorite.filter(name=init_list_name)
        favorite_list = favorite_list.get()
        find = favorite_list.songs_favorite.filter(pk=song.id).count()
        if find == 1:
            favorite_list.songs_favorite.remove(song)
        else:
            favorite_list.songs_favorite.add(song)
        favorite_list.save()
    except(KeyError, Song.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True, 'songidlist': ([al.id for al in favorite_list.songs_favorite.all()])})


def songs(request, filter_by):  # TODO 修改修改
    if not request.user.is_authenticated:
        return render(request, 'music/login.html')
    else:
        page_template = 'music/songs_page.html'
        template = 'music/songs.html'
        id_songs_favorite = []
        try:
            # init favorite icon
            favorite_list = request.user.favorite.filter(name=init_list_name)
            if len(favorite_list) == 0:
                favorite_list = FavoriteList(name=init_list_name, user=request.user)
                favorite_list.save()
                favorite_list = request.user.favorite.filter(name=init_list_name)
            favorite_list = favorite_list.get()
            id_songs_favorite = [song.id for song in favorite_list.songs_favorite.all()]
            user_song_list = []
            query = request.GET.get('q')

            # filter all
            user_list = User.objects.all()
            for user in user_list:
                if request.user.username != user.username:  # 除去自己的传檄

                    if query is None:  # 用户没用搜索
                        songs_list = Song.objects.filter(Q(album__user__username=user.username))

                    else:  # 用户搜索
                        songs_list = Song.objects.filter(Q(album__user__username=user.username), (
                                Q(song_title__contains=query) | Q(album__album_title__contains=query))
                                                         )
                    if songs_list:  # 用户有歌曲才添加
                        user_song_list.append((user, songs_list))

            # filter favorite
            if filter_by == 'favorite':
                user_song_list_temp = []
                for (user, songs_list) in user_song_list:

                    if query:  # 如果用户搜索
                        songs_list = songs_list.filter(Q(pk__in=id_songs_favorite),
                                                       (Q(song_title__contains=query) | Q(
                                                           album__album_title__contains=query)))

                    else:  # 如果用户没搜索
                        songs_list = songs_list.filter(Q(pk__in=id_songs_favorite))
                    if songs_list:  # 用户有歌曲才添加
                        user_song_list_temp.append((user, songs_list))

                user_song_list = user_song_list_temp

        except Album.DoesNotExist:
            user_song_list = []

        context = {'user_song_list': user_song_list, 'filter_by': filter_by,
                   'id_songs_favorite': id_songs_favorite,
                   'page_template': page_template}
        if request.is_ajax():
            template = page_template
        return render(request, template, context)


def albums(request, filter_by):
    if not request.user.is_authenticated:
        return render(request, 'music/login.html')
    else:
        id_albums_favorite = []
        try:
            # init favorite icon
            favorite_list = request.user.favorite.filter(name=init_list_name)
            if len(favorite_list) == 0:
                favorite_list = FavoriteList(name=init_list_name, user=request.user)
                favorite_list.save()
                favorite_list = request.user.favorite.filter(name=init_list_name)
            favorite_list = favorite_list.get()
            id_albums_favorite = [album.id for album in favorite_list.albums_favorite.all()]
            user_album_list = []
            query = request.GET.get('q')
            # 按用户分类选出全部专辑
            user_list = User.objects.all()
            for user in user_list:
                if user.username != request.user.username:  # 除去自己的专辑

                    if query is None:  # 用户没搜索
                        albums_list = Album.objects.filter(user=user)
                        user_album_list.append((user, albums_list))

                    else:
                        albums_list = Album.objects.filter(Q(user=user),
                                                           Q(album_title__contains=query) | Q(artist__contains=query))
                        if albums_list:  # 用户存在album才添加
                            user_album_list.append((user, albums_list))

            # filter favorite
            if filter_by == 'favorite':
                user_album_list_temp = []
                for (user, user_albums) in user_album_list:
                    if query:  # 用户搜索
                        albums_list = user_albums.filter(Q(pk__in=id_albums_favorite),
                                                         Q(album_title__contains=query) | Q(artist__contains=query))
                    else:
                        albums_list = user_albums.filter(Q(pk__in=id_albums_favorite))
                    if albums_list:  # 用户存在album才添加
                        user_album_list_temp.append((user, albums_list))
                user_album_list = user_album_list_temp

        except Album.DoesNotExist:
            user_album_list = []

        template = 'music/albums.html'
        page_template = 'music/albums_page.html'
        context = {'user_album_list': user_album_list, 'filter_by': filter_by,
                   'id_albums_favorite': id_albums_favorite,
                   'page_template': page_template}
        if request.is_ajax():
            template = page_template
        return render(request, template, context)


def register(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.is_active = True  # TODO 后续做邮件验证激活
        user.is_staff = False
        user.save()
        # 为每个用户创建一个默认的FavoriteList实例，
        init_list = FavoriteList.objects.create(user=user, name=init_list_name)
        init_list.save()
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            r_albums = Album.objects.filter(user=request.user)
            return render(request, 'music/index.html', {'albums': r_albums})
    context = {
        "form": form,
    }
    return render(request, 'music/registration.html', context)


def logout_user(request):
    logout(request)
    # form = UserForm(request.POST or None)
    # context = {
    #    'form': form
    # }
    return render(request, 'music/login.html')


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return render(request, 'index_base.html')
            else:
                return render(request, 'music/index.html', {'error_message': '你的账号未激活'})
        else:
            return render(request, 'music/index.html', {'error_message': '无效登录'})
    return render(request, 'music/login.html')


# TODO 做一个类似于虾米音乐的网页播放器


def deal_file(myfile, own_dir, uid):
    # 随机生成新的文件名，自定义路径。
    myext = myfile.name.split('.')[-1]
    file_name = '{0}.{1}'.format(uuid.uuid4().hex[:10], myext)
    uid = str(uid)
    cropped_avatar = os.path.join(uid, own_dir, file_name)
    # 相对根目录路径
    file_path = os.path.join(BASE_DIR, "media", uid, own_dir, file_name)
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    if own_dir == 'pic':
        if myext is None or myext not in IMAGE_FILE_TYPES:
            return "fail"
        # 压缩尺寸为W*H 280*300。
        img = Image.open(myfile)
        crop_im = img.resize((280, 300), Image.ANTIALIAS)
        crop_im.save(file_path)
    elif own_dir == 'music_file':
        with open(file_path, 'w+b') as f:
            f.write(myfile.file.getvalue())
        f.close()
    return cropped_avatar


# temp_API
# distribute this guy. if views need ATOMIC_REQUESTS=TRUE,use the hook(transaction.on_commite)
def album_create_intel(request):
    r = img2text_ocr.delay()
