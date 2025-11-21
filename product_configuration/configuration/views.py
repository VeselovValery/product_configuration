from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from .models import ProductType, BasicPrice, OptionsPrice, OptionsGroup


@login_required(login_url='auth/login/', redirect_field_name='')
def index(request):
    if request.method == 'POST':
        product_type_name = request.POST.get('product_type')
        base_name = request.POST.get('base_name')

        # Обработка опций с новой структурой (option_${optionId}_${instanceIndex})
        option_values = {}
        option_names = {}
        for key, value in request.POST.items():
            if key.startswith('option_') and not key.startswith('option_name_'):
                # Формат: option_${optionId}_${instanceIndex} или option_${optionId}
                parts = key.split('_')
                if len(parts) >= 2:
                    option_id = parts[1]
                    instance_index = parts[2] if len(parts) > 2 else '0'
                    instance_key = f"{option_id}_{instance_index}"
                    try:
                        option_values[instance_key] = int(value)
                    except (ValueError, IndexError):
                        pass
            elif key.startswith('option_name_'):
                # Формат: option_name_${optionId}_${instanceIndex}
                parts = key.split('_')
                if len(parts) >= 3:
                    option_id = parts[2]
                    instance_index = parts[3] if len(parts) > 3 else '0'
                    instance_key = f"{option_id}_{instance_index}"
                    option_names[instance_key] = value

        # Получаем объекты
        product_type = ProductType.objects.get(name=product_type_name)
        basic_product = BasicPrice.objects.get(name=base_name)
        full_name_parts = [basic_product.name]
        total_price = basic_product.price

        # Получаем опции из OptionsGroup
        selected_options = []
        
        for instance_key, value in option_values.items():
            option_id = instance_key.split('_')[0]
            
            # Получаем имя опции (либо из select, либо первое из массива)
            option_name = option_names.get(instance_key, None)
            option = OptionsGroup.objects.get(id=option_id)
            
            if option_name is None and option.name and len(option.name) > 0:
                option_name = option.name[0]
            
            selected_options.append({
                'id': option_id,
                'name': option_name or str(option),
                'value': value
            })
            
            # Примечание: OptionsGroup не имеет полей price и part_name,
            # поэтому расчет цены и формирование имени может потребовать дополнительной логики
            # Пока оставляем базовую структуру
            if value != 0:
                # Если нужна цена/part_name, их нужно добавить в модель или использовать связь с OptionsPrice
                pass

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
    # Используем product_type__name так как ForeignKey указывает на поле name
    options = list(OptionsGroup.objects.filter(product_type__name=type_id))
    if not options:
        return JsonResponse([], safe=False)

    # Собираем все возможные имена опций, чтобы получить описания из OptionsPrice
    option_names = set()
    for option in options:
        option_names.update(option.name or [])

    descriptions_map = dict(
        OptionsPrice.objects.filter(name__in=option_names).values_list('name', 'description')
    )

    serialized = []
    for option in options:
        name_list = option.name or []
        description_list = [descriptions_map.get(name, '') for name in name_list]
        serialized.append({
            'id': option.id,
            'name': name_list,
            'description': description_list,
            'max_value': option.max_value,
            'value': option.value or [],
        })

    return JsonResponse(serialized, safe=False)


def create_basic(request):
    return render(request, 'configuration/index.html')


def my_calculations(request):
    return render(request, 'configuration/my_calculation.html')


def find_calculations(request):
    return render(request, 'configuration/find.html')
