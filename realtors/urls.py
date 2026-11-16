from django.urls import path

from . import views

urlpatterns = [
    path('', views.portal, name='realtor_portal'),
    path('join', views.register, name='realtor_register'),
    path('listings/new', views.listing_create, name='realtor_listing_create'),
    path('listings/<int:pk>/edit', views.listing_edit, name='realtor_listing_edit'),
    path('listings/<int:pk>/toggle', views.listing_toggle, name='realtor_listing_toggle'),
    path('listings/<int:pk>/delete', views.listing_delete, name='realtor_listing_delete'),
    path('inquiries', views.inquiries, name='realtor_inquiries'),
    path('profile', views.profile, name='realtor_profile'),
]
