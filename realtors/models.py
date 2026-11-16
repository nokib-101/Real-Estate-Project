from django.conf import settings
from django.db import models
from django.utils import timezone


class Realtor(models.Model):
    # Set for realtors who signed up on the site; admin-created profiles may have no login
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='realtor_profile')
    # Realtors who sign up wait for an admin to approve them before they can publish
    is_approved = models.BooleanField(default=True)
    name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='photos/%Y/%m/%d/')
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=100)
    is_mvp = models.BooleanField(default=False)
    hire_date = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return str(self.name)

