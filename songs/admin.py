from django.contrib import admin
from .models import Category, Artist, Song


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'artist',
        'category',
        'views',
        'downloads',
        'uploaded_at',
    )
    list_filter = ('category', 'artist')
    search_fields = ('title', 'artist__name')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-uploaded_at',)
