from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from songs.sitemaps import SongSitemap
from songs.views import stream_media


sitemaps = {
    'songs': SongSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('songs.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
    path('media/<path:path>', stream_media, name='media'),
]

if settings.DEBUG:
    # Serve static files in DEBUG (dev only)
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
