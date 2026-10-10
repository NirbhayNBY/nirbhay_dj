from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponse, StreamingHttpResponse, Http404
from django.conf import settings

import os
import mimetypes
import re
from pathlib import Path

from .models import Song, Category, Artist


# Helper: return a Page object for a queryset
def get_page_obj(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


# =========================
# HOME PAGE
# =========================
def home(request):
    song_list = Song.objects.select_related('artist', 'category').order_by('-uploaded_at')
    page_obj = get_page_obj(request, song_list, per_page=12)

    categories = Category.objects.all()

    trending_songs = Song.objects.select_related('artist', 'category').order_by(
        '-downloads',
        '-views',
        '-uploaded_at'
    )[:8]

    return render(request, 'songs/home.html', {
        'page_obj': page_obj,
        'categories': categories,
        'trending_songs': trending_songs
    })


def artist_list(request):
    artists = Artist.objects.all()
    page_obj = get_page_obj(request, artists, per_page=12)

    return render(request, 'songs/artist_list.html', {
        'page_obj': page_obj,
    })


def category_list(request):
    categories = Category.objects.all()
    page_obj = get_page_obj(request, categories, per_page=12)

    return render(request, 'songs/category_list.html', {
        'page_obj': page_obj,
    })


def download_list(request):
    song_list = Song.objects.select_related('artist', 'category').order_by(
        '-downloads',
        '-views',
        '-uploaded_at',
    )
    page_obj = get_page_obj(request, song_list, per_page=12)

    return render(request, 'songs/download_list.html', {
        'page_obj': page_obj,
    })


# =========================
# SONG DETAIL PAGE
# =========================
def song_detail(request, slug):
    song = get_object_or_404(Song.objects.select_related('artist', 'category'), slug=slug)

    # increase view count
    song.views += 1
    song.save(update_fields=['views'])

    # RELATED SONGS (same category, exclude current) with select_related
    related_songs = Song.objects.select_related('artist', 'category').filter(
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
    song_list = Song.objects.select_related('artist', 'category').filter(category=category).order_by('-uploaded_at')
    page_obj = get_page_obj(request, song_list, per_page=12)

    return render(request, 'songs/category_detail.html', {
        'category': category,
        'page_obj': page_obj
    })



# =========================
# ARTIST PAGE
# =========================
def artist_detail(request, slug):
    artist = get_object_or_404(Artist, slug=slug)
    song_list = Song.objects.select_related('artist', 'category').filter(artist=artist).order_by('-uploaded_at')
    page_obj = get_page_obj(request, song_list, per_page=12)

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
        results = Song.objects.select_related('artist', 'category').filter(
            Q(title__icontains=query) |
            Q(artist__name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

    page_obj = get_page_obj(request, results, per_page=12)

    return render(request, 'songs/search.html', {
        'query': query,
        'page_obj': page_obj
    })


# =========================
# DOWNLOAD SONG
# =========================
def download_song(request, slug):
    song = get_object_or_404(Song, slug=slug)

    song.downloads += 1
    song.save(update_fields=['downloads'])

    filename = f"{song.title} - {song.artist.name}.mp3"

    response = FileResponse(song.audio_file.open('rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# =========================
# STREAM MEDIA WITH RANGE SUPPORT
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
    """Stream files from MEDIA_ROOT, including byte ranges used by audio players."""
    media_root = Path(settings.MEDIA_ROOT).resolve()
    full_path = (media_root / path).resolve()
    try:
        full_path.relative_to(media_root)
    except ValueError:
        raise Http404("Media not found")

    if not full_path.is_file():
        raise Http404("Media not found")

    file_size = os.path.getsize(full_path)
    content_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'

    range_header = request.META.get('HTTP_RANGE', '').strip()
    if range_header:
        range_match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
        if not range_match or not any(range_match.groups()):
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{file_size}'
            response['Accept-Ranges'] = 'bytes'
            return response

        start_text, end_text = range_match.groups()
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else file_size - 1
        else:
            suffix_length = int(end_text)
            start = max(file_size - suffix_length, 0)
            end = file_size - 1

        if start >= file_size or start > end:
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{file_size}'
            response['Accept-Ranges'] = 'bytes'
            return response

        end = min(end, file_size - 1)
        length = end - start + 1
        response = StreamingHttpResponse(
            _file_iterator(full_path, start, end),
            status=206,
            content_type=content_type,
        )
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        return response

    # No range header; return entire file
    response = StreamingHttpResponse(
        _file_iterator(full_path, 0, file_size - 1),
        content_type=content_type,
    )
    response['Content-Length'] = str(file_size)
    response['Accept-Ranges'] = 'bytes'
    return response


# =========================
# ADMIN DASHBOARD (STAFF ONLY)
# =========================
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone


@staff_member_required
def admin_dashboard(request):
    # Basic stats
    total_songs = Song.objects.count()
    total_artists = Artist.objects.count()
    total_categories = Category.objects.count()

    # Recent uploads
    recent_songs = Song.objects.select_related('artist', 'category').order_by('-uploaded_at')[:10]

    # Top downloads and most viewed
    top_downloads = Song.objects.order_by('-downloads')[:10]
    top_views = Song.objects.order_by('-views')[:10]

    return render(request, 'songs/admin_dashboard.html', {
        'total_songs': total_songs,
        'total_artists': total_artists,
        'total_categories': total_categories,
        'recent_songs': recent_songs,
        'top_downloads': top_downloads,
        'top_views': top_views,
    })
