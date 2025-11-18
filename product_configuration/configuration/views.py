from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import ProductType, BasicPrice
from .forms import BasicConfigForm


@login_required(login_url='auth/login/', redirect_field_name='')
def index(request):
    types = ProductType.objects.filter(status='active')
    return render(request, 'configuration/index.html', {'product_types': types})


def autocomplete_base_products(request):
    query = request.GET.get('q', '')
    type_id = request.GET.get('type_id', '')

    if len(query) < 2 or not type_id:
        return JsonResponse([], safe=False)

    products = BasicPrice.objects.filter(
        title__icontains=query,
        product_type_id=type_id
    ).values_list('title', flat=True)[:10]

    return JsonResponse(list(products), safe=False)


def get_options(request):
    return render(request, 'configuration/index.html')


def create_basic(request):
    return render(request, 'configuration/index.html')


def my_calculations(request):
    return render(request, 'configuration/my_calculation.html')


def find_calculations(request):
    return render(request, 'configuration/find.html')
