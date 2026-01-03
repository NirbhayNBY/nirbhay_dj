from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('artist/<slug:slug>/', views.artist_detail, name='artist_detail'),

    path('song/<slug:slug>/', views.song_detail, name='song_detail'),
    path('download/<slug:slug>/', views.download_song, name='download_song'),

    path('search/', views.search, name='search'),
]
