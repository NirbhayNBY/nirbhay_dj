import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Artist, Category, Song


class SiteBrandingAndConfigTests(TestCase):
    def test_default_database_uses_sqlite_fallback(self):
        self.assertEqual(
            settings.DATABASES['default']['ENGINE'],
            'django.db.backends.sqlite3',
        )

    def test_site_name_is_nbymix(self):
        template = 'NBYmix'
        self.assertIn('NBYmix', template)
        self.assertNotIn('Nirbhay DJ', template)


class SitePageTests(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create(name='DJ Test', slug='dj-test')
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.song = Song.objects.create(
            title='Test Song',
            slug='test-song',
            category=self.category,
            artist=self.artist,
            audio_file='songs/test-song.mp3',
            downloads=5,
            views=3,
        )

    def test_home_page_renders_primary_navigation_and_content(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Song')
        self.assertContains(response, reverse('artist_list'))
        self.assertContains(response, reverse('download_list'))
        self.assertContains(response, reverse('category_list'))

    def test_artist_pages_render(self):
        listing = self.client.get(reverse('artist_list'))
        detail = self.client.get(reverse('artist_detail', args=[self.artist.slug]))

        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, self.artist.name)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, self.song.title)

    def test_category_pages_render(self):
        listing = self.client.get(reverse('category_list'))
        detail = self.client.get(reverse('category_detail', args=[self.category.slug]))

        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, self.category.name)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, self.song.title)

    def test_download_page_lists_most_downloaded_songs_first(self):
        less_downloaded = Song.objects.create(
            title='Less Popular Song',
            slug='less-popular-song',
            category=self.category,
            artist=self.artist,
            audio_file='songs/less-popular-song.mp3',
            downloads=1,
        )

        response = self.client.get(reverse('download_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['page_obj'].object_list),
            [self.song, less_downloaded],
        )
        self.assertContains(response, reverse('download_song', args=[self.song.slug]))

    def test_search_and_song_detail_render(self):
        search_response = self.client.get(reverse('search'), {'q': 'Test Song'})
        detail_response = self.client.get(reverse('song_detail', args=[self.song.slug]))

        self.assertEqual(search_response.status_code, 200)
        self.assertContains(search_response, self.song.title)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, self.category.name)
        self.song.refresh_from_db()
        self.assertEqual(self.song.views, 4)

    def test_admin_dashboard_requires_staff_access(self):
        url = reverse('admin_dashboard')
        self.assertEqual(self.client.get(url).status_code, 302)

        staff_user = get_user_model().objects.create_user(
            username='site-admin',
            password='test-password',
            is_staff=True,
        )
        self.client.force_login(staff_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total songs:')

    def test_download_returns_audio_and_increments_download_count(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.song.audio_file.save(
                    'test-song.mp3',
                    SimpleUploadedFile('test-song.mp3', b'test-audio-data'),
                    save=True,
                )
                response = self.client.get(
                    reverse('download_song', args=[self.song.slug])
                )

                self.assertEqual(response.status_code, 200)
                self.assertIn('attachment;', response['Content-Disposition'])
                self.assertEqual(b''.join(response.streaming_content), b'test-audio-data')

        self.song.refresh_from_db()
        self.assertEqual(self.song.downloads, 6)

    def test_media_endpoint_supports_byte_ranges_and_rejects_invalid_ranges(self):
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                self.song.audio_file.save(
                    'test-song.mp3',
                    SimpleUploadedFile('test-song.mp3', b'test-audio-data'),
                    save=True,
                )
                media_url = reverse('media', args=[self.song.audio_file.name])

                partial_response = self.client.get(
                    media_url,
                    HTTP_RANGE='bytes=5-9',
                )
                self.assertEqual(partial_response.status_code, 206)
                self.assertEqual(partial_response['Content-Range'], 'bytes 5-9/15')
                self.assertEqual(
                    b''.join(partial_response.streaming_content),
                    b'audio',
                )

                invalid_response = self.client.get(
                    media_url,
                    HTTP_RANGE='bytes=50-60',
                )
                self.assertEqual(invalid_response.status_code, 416)

                outside_file = Path(media_root).parent / (
                    f'{Path(media_root).name}-outside.txt'
                )
                outside_file.write_text('private test file')
                try:
                    traversal_response = self.client.get(
                        reverse('media', args=[f'../{outside_file.name}'])
                    )
                    self.assertEqual(traversal_response.status_code, 404)
                finally:
                    outside_file.unlink()
