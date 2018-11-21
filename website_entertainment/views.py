from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from music.forms import UserForm


# Create your views here.


def index(request):
    if not request.user.is_authenticated:
        return render(request,'music/login.html')
    return render(request, 'index_base.html')


