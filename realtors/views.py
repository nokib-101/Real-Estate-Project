from functools import wraps

from django.contrib import auth, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from contacts.models import Contact
from listings.models import Listing
from .forms import PHOTO_FIELDS, ListingForm, RealtorProfileForm, RealtorSignupForm
from .models import Realtor

User = get_user_model()


def realtor_for(user):
    return Realtor.objects.filter(user=user).first() if user.is_authenticated else None


def realtor_required(view):
    """Only approved realtors get in; the view receives their Realtor profile."""
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        realtor = realtor_for(request.user)
        if realtor is None:
            messages.info(request, 'The realtor portal is for realtors. Apply below to join.')
            return redirect('realtor_register')
        if not realtor.is_approved:
            return render(request, 'realtors/pending.html', {'realtor': realtor})
        return view(request, realtor, *args, **kwargs)
    return wrapper


def inquiries_for(realtor):
    listing_ids = realtor.listing_set.values_list('id', flat=True)
    return Contact.objects.filter(listing_id__in=listing_ids).order_by('-contact_date')


def register(request):
    if realtor_for(request.user):
        return redirect('realtor_portal')
    form = RealtorSignupForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            if request.user.is_authenticated:
                user = request.user
                user.first_name, user.last_name, user.email = data['first_name'], data['last_name'], data['email']
                user.save(update_fields=['first_name', 'last_name', 'email'])
            else:
                user = User.objects.create_user(username=data['username'], password=data['password'], email=data['email'],
                                                first_name=data['first_name'], last_name=data['last_name'])
            Realtor.objects.create(user=user, is_approved=False, name=f"{data['first_name']} {data['last_name']}",
                                   email=data['email'], phone=data['phone'], description=data['description'],
                                   photo=data['photo'])
        if not request.user.is_authenticated:
            auth.login(request, user)
        messages.success(request, 'Thanks for applying! We will review your application shortly.')
        return redirect('realtor_portal')
    return render(request, 'realtors/register.html', {'form': form})


@realtor_required
def portal(request, realtor):
    listings = realtor.listing_set.order_by('-list_date')
    inquiries = inquiries_for(realtor)
    week_ago = timezone.now() - timezone.timedelta(days=7)
    context = {
        'realtor': realtor,
        'listings': listings,
        'recent_inquiries': inquiries[:5],
        'stats': {
            'listings': listings.count(),
            'published': listings.filter(is_published=True).count(),
            'inquiries': inquiries.count(),
            'new_inquiries': inquiries.filter(contact_date__gte=week_ago).count(),
        },
    }
    return render(request, 'realtors/portal.html', context)


@realtor_required
def listing_create(request, realtor):
    form = ListingForm(request.POST or None, request.FILES or None, initial={'is_published': True})
    if request.method == 'POST' and form.is_valid():
        listing = form.save(commit=False)
        listing.realtor = realtor
        listing.save()
        messages.success(request, f'"{listing.title}" has been created.')
        return redirect('realtor_portal')
    return render(request, 'realtors/listing_form.html', {'form': form, 'realtor': realtor, 'photo_fields': PHOTO_FIELDS})


@realtor_required
def listing_edit(request, realtor, pk):
    listing = get_object_or_404(Listing, pk=pk, realtor=realtor)
    form = ListingForm(request.POST or None, request.FILES or None, instance=listing)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{listing.title}" has been updated.')
        return redirect('realtor_portal')
    return render(request, 'realtors/listing_form.html',
                  {'form': form, 'realtor': realtor, 'listing': listing, 'photo_fields': PHOTO_FIELDS})


@require_POST
@realtor_required
def listing_toggle(request, realtor, pk):
    listing = get_object_or_404(Listing, pk=pk, realtor=realtor)
    listing.is_published = not listing.is_published
    listing.save(update_fields=['is_published'])
    state = 'published' if listing.is_published else 'hidden from buyers'
    messages.success(request, f'"{listing.title}" is now {state}.')
    return redirect('realtor_portal')


@require_POST
@realtor_required
def listing_delete(request, realtor, pk):
    listing = get_object_or_404(Listing, pk=pk, realtor=realtor)
    title = listing.title
    listing.delete()
    messages.success(request, f'"{title}" has been deleted.')
    return redirect('realtor_portal')


@realtor_required
def inquiries(request, realtor):
    contacts = list(inquiries_for(realtor))
    titles = dict(realtor.listing_set.values_list('id', 'title'))
    for contact in contacts:
        contact.current_title = titles.get(contact.listing_id, contact.listing)
    return render(request, 'realtors/inquiries.html', {'realtor': realtor, 'contacts': contacts})


@realtor_required
def profile(request, realtor):
    form = RealtorProfileForm(request.POST or None, request.FILES or None, instance=realtor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('realtor_profile')
    return render(request, 'realtors/profile.html', {'form': form, 'realtor': realtor})
