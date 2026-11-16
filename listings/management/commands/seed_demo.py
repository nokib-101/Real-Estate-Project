import os
import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from listings.models import Listing
from realtors.models import Realtor

DEMO_DIR = Path(settings.BASE_DIR) / 'demo_data'
MEDIA_SUBDIR = 'demo'

REALTORS = [
    dict(name='Kyle Brown', photo='kyle-brown.jpg', phone='555-555-5555', email='kyle@btrealestate.test', is_mvp=True,
         description='Kyle has helped over 300 families find their home and specialises in modern coastal properties.'),
    dict(name='Jenny Johnson', photo='jenny-johnson.jpg', phone='555-555-5556', email='jenny@btrealestate.test',
         description='Jenny focuses on family homes and first-time buyers, with a decade of local market experience.'),
    dict(name='Mark Hudson', photo='mark-hudson.jpg', phone='555-555-5557', email='mark@btrealestate.test',
         description='Mark covers luxury and architect-designed residences across the West Coast.'),
]

# (title, realtor index, address, city, state, zipcode, price, bedrooms, bathrooms, garage, sqft, lot_size,
#  main photo, extra photos, description)
LISTINGS = [
    ('Modern Villa with Infinity Pool', 0, '22 Ocean Crest Dr', 'Miami', 'FL', '33139', 1250000, 4, '3.5', 2, 3800, '0.6',
     'villa-pool', ['living-open', 'living-gallery', 'bedroom-modern', 'bathroom'],
     'A bright, architect-designed villa with floor-to-ceiling glass, an infinity pool and open-plan living that flows onto the terrace.'),
    ('Craftsman Home with Mountain View', 1, '480 Pine Ridge Rd', 'Boulder', 'CO', '80302', 845000, 3, '2.5', 2, 2600, '0.4',
     'craftsman-dusk', ['living-plants', 'kitchen-white', 'bedroom-classic'],
     'Warm timber craftsman home with vaulted ceilings, a stone fireplace and sweeping views of the Flatirons.'),
    ('Classic Home with Wraparound Porch', 1, '15 Harbor View Ln', 'Charleston', 'SC', '29401', 695000, 4, '3', 2, 3100, '0.8',
     'porch-home', ['living-bright', 'kitchen-white', 'bedroom-classic'],
     'Timeless family home with a wraparound porch, landscaped garden and generous light-filled rooms.'),
    ('Contemporary Hillside Residence', 2, '9 Canyon Vista', 'Los Angeles', 'CA', '90046', 2100000, 5, '4.5', 3, 4500, '0.7',
     'hillside-modern', ['reading-corner', 'living-open', 'bedroom-modern'],
     'Striking contemporary residence set among mature trees, with seamless indoor-outdoor living and city glimpses.'),
    ('Coastal Family Home with Pool', 0, '301 Palm Ave', 'San Diego', 'CA', '92109', 1480000, 4, '3', 2, 3300, '0.5',
     'coastal-pool', ['living-gallery', 'studio-dining', 'bathroom'],
     'Relaxed coastal living minutes from the beach, with a resort-style pool and wide verandas.'),
    ('Charming Country Cottage', 1, '7 Elm Street', 'Portland', 'ME', '04101', 389000, 2, '1.5', 1, 1400, '0.3',
     'cottage', ['living-plants', 'reading-corner', 'bedroom-classic'],
     'A storybook cottage with a red roof, cosy rooms and a flower-filled front garden. Move-in ready.'),
    ('Brick Two-Story with Double Garage', 2, '1120 Oakwood Blvd', 'Austin', 'TX', '78704', 579000, 4, '2.5', 2, 2800, '0.3',
     'brick-two-story', ['living-bright', 'kitchen-white', 'bedroom-modern'],
     'Spacious two-story brick home on a quiet tree-lined street, with a double garage and a large backyard.'),
    ('Minimalist Pool House', 0, '55 Desert Bloom Way', 'Scottsdale', 'AZ', '85251', 1150000, 3, '3', 2, 2900, '0.5',
     'minimal-pool-house', ['living-open', 'studio-dining', 'bathroom'],
     'Clean-lined modern home with a private pool, rooftop terrace and abundant natural light.'),
    ('Urban Modern Townhouse', 2, '210 Pike Street', 'Seattle', 'WA', '98101', 925000, 3, '2.5', 1, 2100, '0.1',
     'urban-townhouse', ['living-gallery', 'reading-corner', 'bedroom-modern'],
     'Design-forward townhouse with timber accents, close to Pike Place Market and downtown amenities.'),
]


# Approximate map positions for the demo listings (neighbourhood level)
COORDINATES = {
    'Modern Villa with Infinity Pool': ('25.782600', '-80.134100'),
    'Craftsman Home with Mountain View': ('40.017600', '-105.279700'),
    'Classic Home with Wraparound Porch': ('32.776500', '-79.931100'),
    'Contemporary Hillside Residence': ('34.103000', '-118.364000'),
    'Coastal Family Home with Pool': ('32.797700', '-117.240000'),
    'Charming Country Cottage': ('43.659100', '-70.256800'),
    'Brick Two-Story with Double Garage': ('30.244000', '-97.771000'),
    'Minimalist Pool House': ('33.494200', '-111.926100'),
    'Urban Modern Townhouse': ('47.610100', '-122.342100'),
}


class Command(BaseCommand):
    help = 'Load demo realtors and listings (only into an empty database) and create the admin user from env vars.'

    def handle(self, *args, **options):
        self.copy_demo_media()
        if Listing.objects.exists():
            self.stdout.write('Listings already exist; demo data not loaded.')
        else:
            self.load_demo_data()
        self.fill_coordinates()
        self.ensure_superuser()

    def copy_demo_media(self):
        # Copied on every start: Render's free plan doesn't keep files written at runtime
        target = Path(settings.MEDIA_ROOT) / MEDIA_SUBDIR
        target.mkdir(parents=True, exist_ok=True)
        for folder in ('photos', 'realtors'):
            for src in (DEMO_DIR / folder).glob('*.jpg'):
                dest = target / src.name
                if not dest.exists():
                    shutil.copyfile(src, dest)

    def load_demo_data(self):
        realtors = [Realtor.objects.create(**{**r, 'photo': f'{MEDIA_SUBDIR}/{r["photo"]}'}) for r in REALTORS]
        for (title, realtor, address, city, state, zipcode, price, bedrooms, bathrooms, garage, sqft, lot_size,
             main, extras, description) in reversed(LISTINGS):  # first listing ends up newest
            photos = {f'photo_{i}': f'{MEDIA_SUBDIR}/{name}.jpg' for i, name in enumerate(extras, start=1)}
            Listing.objects.create(
                realtor=realtors[realtor], title=title, address=address, city=city, state=state, zipcode=zipcode,
                price=price, bedrooms=bedrooms, bathrooms=Decimal(bathrooms), garage=garage, sqft=sqft,
                lot_size=Decimal(lot_size), photo_main=f'{MEDIA_SUBDIR}/{main}.jpg', description=description,
                **photos,
            )
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(REALTORS)} realtors and {len(LISTINGS)} listings.'))

    def fill_coordinates(self):
        # Also covers databases seeded before listings had map coordinates
        for title, (lat, lng) in COORDINATES.items():
            Listing.objects.filter(title=title, latitude__isnull=True).update(
                latitude=Decimal(lat), longitude=Decimal(lng))

    def ensure_superuser(self):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
        if not username or not password:
            return
        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, password=password,
                                          email=os.getenv('DJANGO_SUPERUSER_EMAIL', ''))
            self.stdout.write(self.style.SUCCESS(f'Created admin user "{username}".'))
