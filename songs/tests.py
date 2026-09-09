from django.conf import settings
from django.test import SimpleTestCase


class SiteBrandingAndConfigTests(SimpleTestCase):
    def test_default_database_uses_sqlite_fallback(self):
        self.assertEqual(
            settings.DATABASES['default']['ENGINE'],
            'django.db.backends.sqlite3',
        )

    def test_site_name_is_nbymix(self):
        template = 'NBYmix'
        self.assertIn('NBYmix', template)
        self.assertNotIn('Nirbhay DJ', template)

# Create your tests here.
