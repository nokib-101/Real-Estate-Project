import io
import shutil
import tempfile
from unittest import mock

from django.contrib.admin.sites import site as admin_site
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from contacts.models import Contact
from listings.models import Listing
from listings.tests import make_listing, make_realtor
from .models import Realtor

User = get_user_model()
MEDIA = tempfile.mkdtemp()


def image_file(name='photo.jpg', size=(40, 30)):
    buf = io.BytesIO()
    Image.new('RGB', size, (37, 99, 235)).save(buf, 'JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


def listing_data(**overrides):
    data = {
        'title': 'Sunny Loft', 'description': 'Light everywhere', 'price': '450000', 'bedrooms': '2',
        'bathrooms': '1.5', 'garage': '1', 'sqft': '1200', 'lot_size': '0.1', 'address': '5 Main St',
        'city': 'Denver', 'state': 'CO', 'zipcode': '80202', 'latitude': '39.739200', 'longitude': '-104.990300',
        'is_published': 'on',
    }
    data.update(overrides)
    return data


@override_settings(MEDIA_ROOT=MEDIA)
class RealtorTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def make_realtor_user(self, username='agent', approved=True):
        user = User.objects.create_user(username, password='Str0ng-Passw0rd!', first_name='Ann', last_name='Agent',
                                        email=f'{username}@realty.test')
        realtor = make_realtor(user=user, is_approved=approved)
        return user, realtor


class SignupTests(RealtorTestCase):
    def signup_data(self, **overrides):
        data = {'first_name': 'Rita', 'last_name': 'Realtor', 'username': 'rita', 'email': 'rita@realty.test',
                'password': 'Str0ng-Passw0rd!', 'password2': 'Str0ng-Passw0rd!', 'phone': '555-0101',
                'description': 'Downtown specialist', 'photo': image_file()}
        data.update(overrides)
        return data

    def test_signup_creates_pending_realtor_and_logs_in(self):
        response = self.client.post(reverse('realtor_register'), self.signup_data())
        self.assertRedirects(response, reverse('realtor_portal'), fetch_redirect_response=False)
        realtor = Realtor.objects.get(user__username='rita')
        self.assertFalse(realtor.is_approved)
        self.assertEqual((realtor.name, realtor.email), ('Rita Realtor', 'rita@realty.test'))
        # pending realtors see the waiting page, not the portal
        self.assertContains(self.client.get(reverse('realtor_portal')), 'being reviewed')

    def test_signup_rejects_weak_password_and_taken_username(self):
        User.objects.create_user('rita', password='x')
        response = self.client.post(reverse('realtor_register'), self.signup_data(password='123', password2='123'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertIn('password', response.context['form'].errors)
        self.assertFalse(Realtor.objects.exists())

    def test_logged_in_buyer_can_apply_without_new_account(self):
        buyer = User.objects.create_user('bob', password='x', email='bob@b.test')
        self.client.force_login(buyer)
        data = self.signup_data()
        for name in ('username', 'password', 'password2'):
            data.pop(name)
        self.client.post(reverse('realtor_register'), data)
        self.assertEqual(Realtor.objects.get().user, buyer)
        self.assertEqual(User.objects.count(), 1)

    def test_pending_realtors_hidden_from_about_page(self):
        self.make_realtor_user('pending', approved=False)
        self.assertEqual(list(self.client.get(reverse('about')).context['realtors']), [])

    def test_admin_action_approves(self):
        _, realtor = self.make_realtor_user(approved=False)
        admin = User.objects.create_superuser('boss', password='x')
        self.client.force_login(admin)
        self.client.post(reverse('admin:realtors_realtor_changelist'),
                         {'action': 'approve_realtors', '_selected_action': [realtor.pk]})
        realtor.refresh_from_db()
        self.assertTrue(realtor.is_approved)


class PortalAccessTests(RealtorTestCase):
    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse('realtor_portal'))
        self.assertTrue(response['Location'].startswith(reverse('login')))

    def test_buyer_redirected_to_application(self):
        self.client.force_login(User.objects.create_user('bob', password='x'))
        self.assertRedirects(self.client.get(reverse('realtor_portal')), reverse('realtor_register'),
                             fetch_redirect_response=False)

    def test_pending_realtor_cannot_create_listing(self):
        user, _ = self.make_realtor_user(approved=False)
        self.client.force_login(user)
        self.client.post(reverse('realtor_listing_create'), {**listing_data(), 'photo_main': image_file()})
        self.assertFalse(Listing.objects.exists())

    def test_realtor_login_lands_in_portal(self):
        self.make_realtor_user()
        response = self.client.post(reverse('login'), {'username': 'agent', 'password': 'Str0ng-Passw0rd!'})
        self.assertRedirects(response, reverse('realtor_portal'), fetch_redirect_response=False)


class ListingManagementTests(RealtorTestCase):
    def setUp(self):
        self.user, self.realtor = self.make_realtor_user()
        self.client.force_login(self.user)
        self.other = make_listing(make_realtor(name='Other Agent'))

    def test_create_listing_with_photos_and_location(self):
        response = self.client.post(reverse('realtor_listing_create'),
                                    {**listing_data(), 'photo_main': image_file(), 'photo_1': image_file('in.jpg')})
        self.assertRedirects(response, reverse('realtor_portal'), fetch_redirect_response=False)
        listing = Listing.objects.get(title='Sunny Loft')
        self.assertEqual(listing.realtor, self.realtor)
        self.assertEqual(len(listing.photos), 2)
        self.assertTrue(listing.has_location)

    def test_create_requires_main_photo_and_rejects_huge_photo(self):
        response = self.client.post(reverse('realtor_listing_create'), listing_data())
        self.assertIn('photo_main', response.context['form'].errors)
        with override_settings(MAX_UPLOAD_PHOTO_MB=0):
            response = self.client.post(reverse('realtor_listing_create'), {**listing_data(), 'photo_main': image_file()})
        self.assertIn('photo_main', response.context['form'].errors)
        self.assertFalse(Listing.objects.filter(title='Sunny Loft').exists())

    def test_edit_own_listing_keeps_existing_photo(self):
        mine = make_listing(self.realtor)
        response = self.client.post(reverse('realtor_listing_edit', args=[mine.id]),
                                    listing_data(title='Renamed', latitude='', longitude=''))
        self.assertRedirects(response, reverse('realtor_portal'), fetch_redirect_response=False)
        mine.refresh_from_db()
        self.assertEqual((mine.title, mine.photo_main.name), ('Renamed', 'home.jpg'))
        self.assertFalse(mine.has_location)

    def test_cannot_touch_other_realtors_listing(self):
        for name in ('realtor_listing_edit', 'realtor_listing_toggle', 'realtor_listing_delete'):
            method = self.client.get if name == 'realtor_listing_edit' else self.client.post
            self.assertEqual(method(reverse(name, args=[self.other.id])).status_code, 404, name)
        self.assertTrue(Listing.objects.filter(pk=self.other.pk, is_published=True).exists())

    def test_toggle_and_owner_preview_of_hidden_listing(self):
        mine = make_listing(self.realtor)
        self.client.post(reverse('realtor_listing_toggle', args=[mine.id]))
        mine.refresh_from_db()
        self.assertFalse(mine.is_published)
        self.assertContains(self.client.get(reverse('listing', args=[mine.id])), 'only you can see this listing')
        self.client.logout()
        self.assertEqual(self.client.get(reverse('listing', args=[mine.id])).status_code, 404)

    def test_toggle_and_delete_require_post(self):
        mine = make_listing(self.realtor)
        self.assertEqual(self.client.get(reverse('realtor_listing_delete', args=[mine.id])).status_code, 405)
        self.client.post(reverse('realtor_listing_delete', args=[mine.id]))
        self.assertFalse(Listing.objects.filter(pk=mine.pk).exists())

    def test_inquiries_show_only_own_listings(self):
        mine = make_listing(self.realtor, title='My House')
        Contact.objects.create(listing='My House', listing_id=mine.id, name='Buyer One', email='b1@x.test',
                               phone='', message='Love it', user_id=0)
        Contact.objects.create(listing=self.other.title, listing_id=self.other.id, name='Buyer Two',
                               email='b2@x.test', phone='', message='Hi', user_id=0)
        response = self.client.get(reverse('realtor_inquiries'))
        self.assertContains(response, 'Buyer One')
        self.assertNotContains(response, 'Buyer Two')
        self.assertEqual(self.client.get(reverse('realtor_portal')).context['stats']['inquiries'], 1)

    def test_profile_update(self):
        response = self.client.post(reverse('realtor_profile'), {'name': 'Ann A. Agent', 'phone': '555-9999',
                                                                 'email': 'ann@realty.test', 'description': 'Hi'})
        self.assertRedirects(response, reverse('realtor_profile'), fetch_redirect_response=False)
        self.realtor.refresh_from_db()
        self.assertEqual((self.realtor.name, self.realtor.phone), ('Ann A. Agent', '555-9999'))


@override_settings(MEDIA_ROOT=MEDIA, MEDIA_URL='/media/')
class CloudinaryStorageTests(TestCase):
    def setUp(self):
        from btre.storage import MediaStorage
        self.storage = MediaStorage()

    def test_uploads_go_to_cloudinary_with_unique_names(self):
        with mock.patch('btre.storage.cloudinary.uploader.upload') as upload:
            name = self.storage.save('photos/2026/11/16/house.jpg', ContentFile(b'img', name='house.jpg'), max_length=100)
        self.assertRegex(name, r'^photos/2026/11/16/house_[a-z0-9]{7}\.jpg$')
        self.assertEqual(upload.call_args.kwargs['public_id'], 'btre/' + name[:-4])

    def test_cloudinary_url(self):
        with mock.patch.dict('os.environ', {'CLOUDINARY_URL': 'cloudinary://1:2@demo-cloud'}):
            import cloudinary
            cloudinary.reset_config()
            url = self.storage.url('photos/x/house_abc1234.jpg')
        self.assertEqual(url, 'https://res.cloudinary.com/demo-cloud/image/upload/f_auto,q_auto/v1/btre/photos/x/house_abc1234')

    def test_demo_photos_stay_local(self):
        with mock.patch('btre.storage.cloudinary.uploader.upload') as upload:
            name = self.storage.save('demo/villa.jpg', ContentFile(b'img'))
        upload.assert_not_called()
        self.assertEqual(self.storage.url(name), '/media/' + name)
        self.assertTrue(self.storage.exists(name))

    def test_long_names_fit_field(self):
        with mock.patch('btre.storage.cloudinary.uploader.upload'):
            name = self.storage.save('photos/2026/11/16/' + 'a' * 120 + '.jpg', ContentFile(b'x'), max_length=100)
        self.assertLessEqual(len(name), 100)

    def test_delete_failure_is_logged_not_raised(self):
        with mock.patch('btre.storage.cloudinary.uploader.destroy', side_effect=OSError('down')):
            with self.assertLogs('btre.storage', level='ERROR'):
                self.storage.delete('photos/x/house_abc1234.jpg')

    def test_settings_switch_to_cloudinary_when_configured(self):
        import importlib
        import btre.settings as s
        with mock.patch.dict('os.environ', {'CLOUDINARY_URL': 'cloudinary://1:2@demo-cloud'}):
            importlib.reload(s)
            self.assertEqual(s.STORAGES['default']['BACKEND'], 'btre.storage.MediaStorage')
        importlib.reload(s)
        self.assertEqual(s.STORAGES['default']['BACKEND'], 'django.core.files.storage.FileSystemStorage')
