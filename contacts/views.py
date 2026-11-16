import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404, redirect

from listings.models import Listing
from .models import Contact

logger = logging.getLogger(__name__)


def contact(request):
    if request.method != 'POST':
        return redirect('listings')

    # The listing and its realtor come from the database, never from the form,
    # so the email recipient and property title can't be forged.
    listing = get_object_or_404(Listing, pk=request.POST.get('listing_id', ''), is_published=True)
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    inq_message = request.POST.get('message', '').strip()

    if not name or not email:
        messages.error(request, 'Please enter your name and email')
        return redirect('listing', listing_id=listing.id)
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, 'Please enter a valid email address')
        return redirect('listing', listing_id=listing.id)

    # Only a logged-in user's own id is recorded; anonymous inquiries use 0
    user_id = request.user.id if request.user.is_authenticated else 0

    # check already made inquiry
    if request.user.is_authenticated and Contact.objects.filter(listing_id=listing.id, user_id=user_id).exists():
        messages.error(request, 'You have already made an inquiry for this listing')
        return redirect('listing', listing_id=listing.id)

    Contact.objects.create(listing=listing.title, listing_id=listing.id, name=name, email=email,
                           phone=phone, message=inq_message, user_id=user_id)

    # send email; the inquiry is already saved, so a mail failure must not break the page
    try:
        EmailMessage(
            subject=f'Property Listing Inquiry: {listing.title}',
            body=(f'There has been an inquiry for {listing.title}.\n\n'
                  f'Name: {name}\nEmail: {email}\nPhone: {phone or "-"}\n\n'
                  f'Message:\n{inq_message or "-"}\n'),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[listing.realtor.email],
            reply_to=[email],
        ).send()
    except Exception:
        logger.exception('Failed to send inquiry email for listing %s', listing.id)

    messages.success(request, 'Your request has been submitted, a realtor will get back to you soon')
    return redirect('listing', listing_id=listing.id)
