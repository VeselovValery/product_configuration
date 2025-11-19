from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import ProductType, BasicPrice, OptionsPrice


@login_required(login_url='auth/login/', redirect_field_name='')
def index(request):
    if request.method == 'POST':
        product_type_name = request.POST.get('product_type')
        base_name = request.POST.get('base_name')

        option_values = {}
        for key, value in request.POST.items():
            if key.startswith('option_'):
                option_id = key.split('_')[1]
                option_values[option_id] = value

        # Получаем объекты
        product_type = ProductType.objects.get(name=product_type_name)
        basic_product = BasicPrice.objects.get(name=base_name)
        full_name_parts = [basic_product.name]
        total_price = basic_product.price

        # Получаем опции
        selected_options = []
        for opt_id, value in option_values.items():
            option = OptionsPrice.objects.get(id=opt_id)
            selected_options.append({
                'name': option.name,
                'value': value
            })
            if option.value != 0:
                full_name_parts.append(option.part_name)
                total_price += option.price * int(value)
        full_name = ''.join(full_name_parts)

        return JsonResponse({
            'product_type': product_type.name,
            'base_name': base_name,
            'selected_options': selected_options,
            'full_name': full_name,
            'total_price': total_price
        })
    else:
        types = ProductType.objects.filter(status='active')
        return render(request, 'configuration/index.html', {'product_types': types})


def autocomplete_base_products(request):
    query = request.GET.get('q', '')
    type_id = request.GET.get('type_id', '')

    if len(query) < 2 or not type_id:
        return JsonResponse([], safe=False)

    products = BasicPrice.objects.filter(
        name__icontains=query,
        product_type_id=type_id
    ).values_list('name', flat=True)[:10]
    return JsonResponse(list(products), safe=False)


def get_options(request):
    type_id = request.GET.get('type_id')
    if not type_id:
        return JsonResponse([], safe=False)
    options = OptionsPrice.objects.filter(product_type_id=type_id).values('id', 'name', 'description', 'value')
    return JsonResponse(list(options), safe=False)


def create_basic(request):
    return render(request, 'configuration/index.html')


def my_calculations(request):
    return render(request, 'configuration/my_calculation.html')


def find_calculations(request):
    return render(request, 'configuration/find.html')
