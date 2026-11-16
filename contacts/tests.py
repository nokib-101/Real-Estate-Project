from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from listings.tests import make_listing, make_realtor
from .models import Contact

User = get_user_model()


class ContactInquiryTests(TestCase):
    def setUp(self):
        self.listing = make_listing(make_realtor())
        self.form = {
            'listing_id': self.listing.id, 'name': 'Bob Buyer', 'email': 'bob@buyer.test',
            'phone': '123', 'message': 'Is it still available?',
        }

    def post(self, **overrides):
        return self.client.post(reverse('contact'), {**self.form, **overrides})

    def test_inquiry_is_saved_and_emailed_to_listing_realtor(self):
        response = self.post()
        self.assertRedirects(response, reverse('listing', args=[self.listing.id]), fetch_redirect_response=False)
        self.assertEqual(Contact.objects.get().listing, 'Lake House')
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['jane@realty.test'])
        self.assertEqual(email.reply_to, ['bob@buyer.test'])
        self.assertIn('Is it still available?', email.body)

    def test_recipient_and_title_cannot_be_forged(self):
        self.post(realtor_email='victim@spam.test', listing='BUY CHEAP PILLS')
        self.assertEqual(mail.outbox[0].to, ['jane@realty.test'])
        self.assertNotIn('PILLS', mail.outbox[0].subject + mail.outbox[0].body)

    def test_anonymous_user_cannot_set_user_id(self):
        victim = User.objects.create_user('victim', password='x')
        self.post(user_id=victim.id)
        self.assertEqual(Contact.objects.get().user_id, 0)

    def test_unknown_or_unpublished_listing_is_404(self):
        self.assertEqual(self.post(listing_id=9999).status_code, 404)
        self.listing.is_published = False
        self.listing.save()
        self.assertEqual(self.post().status_code, 404)

    def test_missing_fields_do_not_crash(self):
        response = self.client.post(reverse('contact'), {'listing_id': self.listing.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), 0)

    def test_invalid_email_is_rejected(self):
        self.post(email='not-an-email')
        self.assertEqual(Contact.objects.count(), 0)

    def test_get_request_redirects_instead_of_crashing(self):
        self.assertEqual(self.client.get(reverse('contact')).status_code, 302)

    def test_email_failure_still_saves_inquiry(self):
        from unittest import mock
        with mock.patch('contacts.views.EmailMessage.send', side_effect=OSError('SMTP down')):
            response = self.post()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), 1)

    def test_logged_in_user_duplicate_inquiry_is_blocked(self):
        user = User.objects.create_user('bob', password='x')
        self.client.force_login(user)
        self.post()
        self.post()
        self.assertEqual(Contact.objects.filter(user_id=user.id).count(), 1)
