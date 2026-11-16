from django.shortcuts import render
from django.http import HttpResponse
from listings.choices import price_choices, bedroom_choices, state_choices

from listings.models import Listing
from realtors.models import Realtor

# Create your views here.

def index(request):
    published = Listing.objects.filter(is_published=True)
    listings = published.order_by('-list_date').select_related('realtor')[:3]
    context = {
        'listings': listings,
        'listing_count': published.count(),
        'city_count': published.values('city').distinct().count(),
        'realtor_count': Realtor.objects.count(),
        'top_cities': published.values_list('city', flat=True).distinct().order_by('city')[:6],
        'state_choices': state_choices,
        'bedroom_choices': bedroom_choices,
        'price_choices' : price_choices

    }
    return render(request,'pages/index.html',context)

def about(request):
    # get all realtors 
    realtors = Realtor.objects.order_by('-hire_date')

    # set mvp 
    mvp_realtors = Realtor.objects.all().filter(is_mvp=True)

    context = {
        'realtors': realtors,
        'mvp_realtors': mvp_realtors

    }

    return render(request,'pages/about.html',context)


