"""Media storage: uploaded photos go to Cloudinary, demo photos stay local.

Render's free plan wipes files written at runtime, so photos uploaded by
realtors or in the admin are stored on Cloudinary instead. The demo photos
that ship with the app (names starting with ``demo/``, see seed_demo) are
still served from MEDIA_ROOT, so existing demo listings keep working.

Enabled when the CLOUDINARY_URL environment variable is set (see settings).
"""
import logging
import os

import cloudinary
import cloudinary.uploader
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.crypto import get_random_string
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)

CLOUDINARY_FOLDER = 'btre'
LOCAL_PREFIX = 'demo/'


@deconstructible
class MediaStorage(Storage):
    def __init__(self):
        self.local = FileSystemStorage()

    @staticmethod
    def _is_local(name):
        return name.replace('\\', '/').startswith(LOCAL_PREFIX)

    @staticmethod
    def _public_id(name):
        # Stored names keep their extension; Cloudinary public ids don't
        base, _ = os.path.splitext(name.replace('\\', '/'))
        return f'{CLOUDINARY_FOLDER}/{base}'

    def get_available_name(self, name, max_length=None):
        if self._is_local(name):
            return self.local.get_available_name(name, max_length=max_length)
        # Cloudinary can't cheaply check for existing names, so make every
        # upload unique with a random suffix (trimmed to fit the field)
        base, ext = os.path.splitext(name.replace('\\', '/'))
        suffix = f'_{get_random_string(7).lower()}'
        if max_length:
            base = base[:max_length - len(suffix) - len(ext)]
        return f'{base}{suffix}{ext}'

    def _save(self, name, content):
        if self._is_local(name):
            return self.local._save(name, content)
        if hasattr(content, 'seek'):
            content.seek(0)
        cloudinary.uploader.upload(content, public_id=self._public_id(name), resource_type='image', overwrite=True)
        return name.replace('\\', '/')

    def url(self, name):
        if self._is_local(name):
            return self.local.url(name)
        # f_auto/q_auto: Cloudinary serves the best format and quality per browser
        return cloudinary.CloudinaryImage(self._public_id(name)).build_url(
            secure=True, transformation=[{'fetch_format': 'auto', 'quality': 'auto'}])

    def exists(self, name):
        if self._is_local(name):
            return self.local.exists(name)
        return False  # names are made unique in get_available_name

    def delete(self, name):
        if self._is_local(name):
            return self.local.delete(name)
        try:
            cloudinary.uploader.destroy(self._public_id(name), invalidate=True)
        except Exception:
            logger.exception('Could not delete %s from Cloudinary', name)
