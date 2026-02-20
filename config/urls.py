from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from songs.sitemaps import SongSitemap


sitemaps = {
    'songs': SongSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('songs.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
]


if settings.DEBUG:
    # Use a development media streaming view that supports HTTP Range requests
    # so audio/video seeking works when DEBUG=True.
    from songs.views import stream_media
    urlpatterns += [
        path('media/<path:path>', stream_media, name='media')
    ]

    # Serve static files in DEBUG (dev only)
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
