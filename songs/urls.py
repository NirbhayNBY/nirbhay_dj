from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('artists/', views.artist_list, name='artist_list'),
    path('downloads/', views.download_list, name='download_list'),
    path('categories/', views.category_list, name='category_list'),

    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('artist/<slug:slug>/', views.artist_detail, name='artist_detail'),

    path('song/<slug:slug>/', views.song_detail, name='song_detail'),
    path('download/<slug:slug>/', views.download_song, name='download_song'),

    path('search/', views.search, name='search'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
