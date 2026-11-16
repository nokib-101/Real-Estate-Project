from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme
from contacts.models import Contact
from listings.models import Listing
from realtors.models import Realtor


User = get_user_model()


def register(request):
    if request.method == "POST":
        # Get form values
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password:
            messages.error(request, 'Please fill in all required fields')
            return redirect('register')
        # check password match
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')
        # check username
        if User.objects.filter(username=username).exists():
            messages.error(request, 'That username is taken')
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'That email is being used')
            return redirect('register')
        # apply the password rules from AUTH_PASSWORD_VALIDATORS
        candidate = User(username=username, email=email, first_name=first_name, last_name=last_name)
        try:
            validate_password(password, user=candidate)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('register')

        User.objects.create_user(username=username, password=password, email=email,
                                 first_name=first_name, last_name=last_name)
        messages.success(request, 'You are now registered and can log in')
        return redirect('login')
    else:
        return render(request, 'accounts/register.html')

def login(request):
    if request.method == "POST":
        # Login User
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are now logged in')
            # go back to the page that asked for login, if it's on this site
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                                            require_https=request.is_secure()):
                return redirect(next_url)
            if Realtor.objects.filter(user=user).exists():
                return redirect('realtor_portal')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    else:
        return render(request, 'accounts/login.html')


def logout(request):
    if request.method == "POST":
        auth.logout(request)
        messages.success(request, 'Logout successful')
    return redirect('index')

@login_required
def dashboard(request):
    user_contacts = list(Contact.objects.order_by('-contact_date').filter(user_id=request.user.id))
    # Attach each inquiry's listing (if it's still published) for photos and details
    listings = Listing.objects.filter(id__in=[c.listing_id for c in user_contacts], is_published=True).select_related('realtor')
    by_id = {listing.id: listing for listing in listings}
    for contact in user_contacts:
        contact.listing_obj = by_id.get(contact.listing_id)
    recommended = (Listing.objects.filter(is_published=True).exclude(id__in=by_id)
                   .select_related('realtor').order_by('-list_date')[:3])
    context = {
        'contacts': user_contacts,
        'recommended': recommended,
    }
    return render(request, 'accounts/dashboard.html', context)
