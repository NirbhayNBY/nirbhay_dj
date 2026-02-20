from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator

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
from django.conf import settings
from django.http import StreamingHttpResponse, Http404
import os
import mimetypes
import re

def download_song(request, slug):
    song = get_object_or_404(Song, slug=slug)

    song.downloads += 1
    song.save(update_fields=['downloads'])

    filename = f"{song.title} - {song.artist.name}.mp3"

    response = FileResponse(song.audio_file.open('rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# =========================
# STREAM MEDIA WITH RANGE SUPPORT (DEV ONLY)
# =========================
def _file_iterator(path, start=0, end=None, chunk_size=8192):
    with open(path, 'rb') as f:
        f.seek(start)
        remaining = None if end is None else (end - start + 1)
        while True:
            read_size = chunk_size if remaining is None else min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            yield data
            if remaining is not None:
                remaining -= len(data)
                if remaining <= 0:
                    break


def stream_media(request, path):
    """Stream files from MEDIA_ROOT supporting HTTP Range requests.

    Use only in development (DEBUG=True). Returns 206 for ranged requests.
    """
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(full_path):
        raise Http404("Media not found")

    file_size = os.path.getsize(full_path)
    content_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'

    range_header = request.META.get('HTTP_RANGE', '').strip()
    if range_header:
        m = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else file_size - 1
            if end >= file_size:
                end = file_size - 1
            length = end - start + 1

            resp = StreamingHttpResponse(_file_iterator(full_path, start, end), status=206, content_type=content_type)
            resp['Content-Length'] = str(length)
            resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            resp['Accept-Ranges'] = 'bytes'
            return resp

    # No range header; return entire file
    resp = StreamingHttpResponse(_file_iterator(full_path, 0, file_size - 1), content_type=content_type)
    resp['Content-Length'] = str(file_size)
    resp['Accept-Ranges'] = 'bytes'
    return resp
