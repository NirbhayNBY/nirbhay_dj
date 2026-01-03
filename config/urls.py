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
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
