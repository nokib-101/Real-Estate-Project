from django.test import TestCase
from django.urls import reverse

from realtors.models import Realtor
from .models import Listing


def make_realtor(**kwargs):
    return Realtor.objects.create(name='Jane Agent', photo='realtor.jpg', phone='555', email='jane@realty.test', **kwargs)


def make_listing(realtor, **kwargs):
    fields = dict(
        realtor=realtor, title='Lake House', address='1 Lake Rd', city='Boston', state='MA',
        zipcode='02101', description='Lovely lake view', price=500000, bedrooms=3,
        bathrooms=2, sqft=1800, lot_size=0.5, photo_main='home.jpg',
    )
    fields.update(kwargs)
    return Listing.objects.create(**fields)


class ListingVisibilityTests(TestCase):
    def setUp(self):
        realtor = make_realtor()
        self.published = make_listing(realtor)
        self.hidden = make_listing(realtor, title='Secret Villa', description='Lovely hidden villa', is_published=False)

    def test_unpublished_listing_detail_is_404(self):
        response = self.client.get(reverse('listing', args=[self.hidden.id]))
        self.assertEqual(response.status_code, 404)

    def test_published_listing_detail_is_shown(self):
        response = self.client.get(reverse('listing', args=[self.published.id]))
        self.assertContains(response, 'Lake House')

    def test_search_excludes_unpublished_listings(self):
        response = self.client.get(reverse('search'), {'keywords': 'Lovely'})
        self.assertEqual(list(response.context['listings']), [self.published])


class SearchInputTests(TestCase):
    def setUp(self):
        make_listing(make_realtor())

    def test_non_numeric_price_and_bedrooms_are_ignored(self):
        response = self.client.get(reverse('search'), {'price': 'abc', 'bedrooms': '2x'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['listings']), 1)

    def test_numeric_filters_still_work(self):
        response = self.client.get(reverse('search'), {'price': '100000'})
        self.assertEqual(len(response.context['listings']), 0)


class RealtorDeletionTests(TestCase):
    def test_realtor_with_listings_cannot_be_deleted(self):
        from django.db.models import ProtectedError
        realtor = make_realtor()
        make_listing(realtor)
        with self.assertRaises(ProtectedError):
            realtor.delete()
