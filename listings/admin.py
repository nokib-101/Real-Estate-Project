from django.contrib import admin

# Register your models here.
from .models import Listing 

class ListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_published', 'price', 'list_date', 'realtor')

    list_display_links = ('id','title')
    list_filter = ('realtor',)
    list_editable = ('is_published',)
    search_fields = ('title','address','city','state','zipcode','price')
    list_per_page = 25
    fieldsets = (
        (None, {'fields': ('realtor', 'title', 'description', 'is_published', 'list_date')}),
        ('Location', {'fields': ('address', 'city', 'state', 'zipcode', 'latitude', 'longitude')}),
        ('Details', {'fields': ('price', 'bedrooms', 'bathrooms', 'garage', 'sqft', 'lot_size')}),
        ('Photos', {'fields': ('photo_main', 'photo_1', 'photo_2', 'photo_3', 'photo_4', 'photo_5', 'photo_6')}),
    )
    




admin.site.register(Listing, ListingAdmin)



