from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Song


class SongSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Song.objects.all()

    def location(self, obj):
        return reverse('song_detail', args=[obj.slug])
