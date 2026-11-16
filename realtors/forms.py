from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import UploadedFile

from listings.models import Listing
from .models import Realtor

User = get_user_model()

PHOTO_FIELDS = ('photo_main', 'photo_1', 'photo_2', 'photo_3', 'photo_4', 'photo_5', 'photo_6')


def style_fields(form):
    """Give each widget the matching Bootstrap 5 class."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            css = 'form-check-input'
        elif isinstance(widget, forms.Select):
            css = 'form-select'
        else:
            css = 'form-control'
        widget.attrs['class'] = (widget.attrs.get('class', '') + ' ' + css).strip()


def check_photo_size(photo):
    # Only new uploads: already-saved photos may live on Cloudinary (no size
    # lookup) or be missing locally, and were checked when uploaded
    limit = settings.MAX_UPLOAD_PHOTO_MB
    if isinstance(photo, UploadedFile) and photo.size > limit * 1024 * 1024:
        raise forms.ValidationError(f'Photos must be {limit} MB or smaller.')
    return photo


class RealtorSignupForm(forms.Form):
    """Realtor application. Account fields are only shown to visitors who aren't logged in."""
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    email = forms.EmailField(help_text='Buyers\' inquiries about your listings go to this address.')
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    phone = forms.CharField(max_length=20)
    description = forms.CharField(label='About you', required=False, widget=forms.Textarea(attrs={'rows': 3}),
                                  help_text='A short bio shown on your profile.')
    photo = forms.ImageField(label='Profile photo', help_text='A clear headshot works best.')

    ACCOUNT_FIELDS = ('username', 'password', 'password2')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user if user is not None and user.is_authenticated else None
        if self.user:
            for name in self.ACCOUNT_FIELDS:
                del self.fields[name]
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
        style_fields(self)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('That username is taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        taken = User.objects.filter(email__iexact=email)
        if self.user:
            taken = taken.exclude(pk=self.user.pk)
        if taken.exists():
            raise forms.ValidationError('That email is already used by another account.')
        return email

    def clean_photo(self):
        return check_photo_size(self.cleaned_data.get('photo'))

    def clean(self):
        cleaned = super().clean()
        if not self.user:
            password, password2 = cleaned.get('password'), cleaned.get('password2')
            if password and password2 and password != password2:
                self.add_error('password2', 'Passwords do not match.')
            elif password:
                candidate = User(username=cleaned.get('username', ''), email=cleaned.get('email', ''),
                                 first_name=cleaned.get('first_name', ''), last_name=cleaned.get('last_name', ''))
                try:
                    validate_password(password, user=candidate)
                except forms.ValidationError as e:
                    self.add_error('password', e)
        return cleaned


class RealtorProfileForm(forms.ModelForm):
    class Meta:
        model = Realtor
        fields = ('name', 'phone', 'email', 'description', 'photo')
        labels = {'description': 'About you', 'photo': 'Profile photo'}
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_photo(self):
        return check_photo_size(self.cleaned_data.get('photo'))


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ('title', 'description', 'price', 'bedrooms', 'bathrooms', 'garage', 'sqft', 'lot_size',
                  'address', 'city', 'state', 'zipcode', 'latitude', 'longitude', 'is_published') + PHOTO_FIELDS
        labels = {
            'sqft': 'Living area (sq ft)', 'lot_size': 'Lot size (acres)', 'zipcode': 'ZIP code',
            'is_published': 'Published (visible to buyers)', 'photo_main': 'Main photo',
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from listings.choices import state_choices
        self.fields['state'] = forms.ChoiceField(choices=[('', 'Select a state')] + list(state_choices.items()),
                                                 initial=self.initial.get('state'))
        for i, name in enumerate(PHOTO_FIELDS[1:], start=1):
            self.fields[name].label = f'Photo {i}'
        self.fields['latitude'].help_text = 'Click the map above to set the location, or type coordinates'
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        for name in PHOTO_FIELDS:
            photo = cleaned.get(name)
            try:
                check_photo_size(photo)
            except forms.ValidationError as e:
                self.add_error(name, e)
        if (cleaned.get('latitude') is None) != (cleaned.get('longitude') is None):
            self.add_error('longitude', 'Set both latitude and longitude, or neither.')
        for name, low, high in (('price', 1, 1_000_000_000), ('bedrooms', 0, 50), ('garage', 0, 20), ('sqft', 1, 1_000_000)):
            value = cleaned.get(name)
            if value is not None and not low <= value <= high:
                self.add_error(name, f'Enter a value between {low:,} and {high:,}.')
        return cleaned
