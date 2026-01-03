from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect

from .models import Song, Category, Artist


# =========================
# HOME PAGE
# =========================
def home(request):
    song_list = Song.objects.order_by('-uploaded_at')
    paginator = Paginator(song_list, 12)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    trending_songs = Song.objects.order_by(
        '-downloads',
        '-views',
        '-uploaded_at'
    )[:8]

    return render(request, 'songs/home.html', {
        'page_obj': page_obj,
        'categories': categories,
        'trending_songs': trending_songs
    })


# =========================
# SONG DETAIL PAGE
# =========================
def song_detail(request, slug):
    song = get_object_or_404(Song, slug=slug)

    # increase view count
    song.views += 1
    song.save(update_fields=['views'])
    # RELATED SONGS (same category OR same artist, exclude current)
    related_songs = Song.objects.filter(
        category=song.category
    ).exclude(id=song.id).order_by('-downloads')[:10]

    return render(request, 'songs/song_detail.html', {
        'song': song,
        'related_songs': related_songs
    })

# =========================
# CATEGORY PAGE
# =========================
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    song_list = Song.objects.filter(category=category).order_by('-uploaded_at')

    paginator = Paginator(song_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'songs/category_detail.html', {
        'category': category,
        'page_obj': page_obj
    })


# =========================
# ARTIST PAGE
# =========================
def artist_detail(request, slug):
    artist = get_object_or_404(Artist, slug=slug)
    song_list = Song.objects.filter(artist=artist).order_by('-uploaded_at')

    paginator = Paginator(song_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'songs/artist_detail.html', {
        'artist': artist,
        'page_obj': page_obj
    })


# =========================
# SEARCH PAGE
# =========================
def search(request):
    query = request.GET.get('q')
    results = Song.objects.none()

    if query:
        results = Song.objects.filter(
            Q(title__icontains=query) |
            Q(artist__name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'songs/search.html', {
        'query': query,
        'page_obj': page_obj
    })


# =========================
# DOWNLOAD SONG
# =========================
from django.http import FileResponse

def download_song(request, slug):
    song = get_object_or_404(Song, slug=slug)

    song.downloads += 1
    song.save(update_fields=['downloads'])

    response = FileResponse(song.audio_file.open('rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{song.slug}.mp3"'
    return response