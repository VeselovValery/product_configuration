import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView

from .forms import UploadCSVForm
from .models import ProductType, BasicPrice, OptionsPrice, OptionsGroup, Configuration


MODEL_MAP = {
    'ProductType': ProductType,
    'BasicPrice': BasicPrice,
    'OptionsPrice': OptionsPrice,
    'OptionsGroup': OptionsGroup
}


@login_required(login_url='auth/login/', redirect_field_name='')
def index(request):
    if request.method == 'POST':
        product_type = ProductType.objects.get(name=request.POST.get('product_type'))
        basic_product = BasicPrice.objects.get(name=request.POST.get('base_name'))
        # Обработка опций
        option_values = {}
        option_names = {}
        for key, value in request.POST.items():
            if key.startswith('option_') and not key.startswith('option_name_'):
                # Значение объема подключаемой опции
                # Формат: option_${optionId}_${instanceIndex} или option_${optionId}
                parts = key.split('_')
                if len(parts) >= 2:
                    instance_key = f'{parts[1]}_{parts[2] if len(parts) > 2 else "0"}'
                    option_values[instance_key] = int(value)
            elif key.startswith('option_name_'):
                # Название подключаемой опции
                # Формат: option_name_${optionId}_${instanceIndex}
                parts = key.split('_')
                if len(parts) >= 3:
                    instance_key = f'{parts[2]}_{parts[3] if len(parts) > 3 else "0"}'
                    option_names[instance_key] = value
        full_name_parts = [basic_product.name]  # Составное имя
        total_price = basic_product.price  # Цена опционального оборудования
        # Подгружаем выбранные опции из OptionsPrice
        value_selected_options = dict()
        selected_options = list()
        for instance_key, value in option_values.items():
            if value != 0:
                option_name = option_names.get(instance_key, None)
                option = OptionsPrice.objects.get(name=option_name)
                if option not in selected_options:
                    selected_options.append(option)
                if option_name not in value_selected_options:
                    value_selected_options[option_name] = 0
                value_selected_options[option_name] += value
                total_price += (option.price * value)
                if option.part_name not in full_name_parts:
                    full_name_parts.append(option.part_name)
        # Формирование наименования опционального изделия
        full_name = ''.join(full_name_parts)
        # Запись данных о расчете
        config = Configuration.objects.create(
            product_type=product_type,
            basic_product=basic_product,
            name=full_name,
            cost=total_price,
            author=request.user,
        )
        config.options.set(selected_options)
        config.options_value = [f'{key} - {value}' for key, value in value_selected_options.items()]
        config.save()
        # Возврат названия и цены продукции
        return JsonResponse({
            'full_name': full_name,
            'total_price': total_price
        })
    else:
        types = ProductType.objects.filter(status='active')
        return render(request, 'configuration/index.html', {'product_types': types})


def autocomplete_base_products(request):
    query = request.GET.get('q', '')
    type_id = request.GET.get('type_id', '')
    # Если кол-во введеных символов меньше 2 или не введен Тип продукта
    if len(query) < 2 or not type_id:
        return JsonResponse([], safe=False)
    # Подбираем список продуктов
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


class MyCalculations(LoginRequiredMixin, ListView):
    login_url = 'auth/login/'
    redirect_field_name = ''
    template_name = 'configuration/my_calculation.html'

    def get_queryset(self):
        return Configuration.objects.filter(author__pk=self.kwargs['pk']).select_related(
            'product_type',
            'author'
        )


@login_required(login_url='auth/login/', redirect_field_name='')
def upload_data(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            table_name = form.cleaned_data['table']
            operation = form.cleaned_data['operation']
            file = request.FILES['file']
            model_class = MODEL_MAP.get(table_name)
            if not model_class:
                messages.error(request, 'Неизвестная таблица.')
                return render(request, 'configuration/upload_data.html', {'form': form})
            try:
                decoded_file = file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)

                created_count = 0
                updated_count = 0
                for row in reader:
                    if operation == 'create':
                        model_class.objects.create(**row)
                        created_count += 1
                    elif operation == 'update':
                        lookup_field = 'name'  # или другое уникальное поле
                        lookup_value = row.get(lookup_field)
                        if lookup_value:
                            model_class.objects.filter(**{lookup_field: lookup_value}).update(**{k: v for k, v in row.items() if k != lookup_field})
                            updated_count += 1
                messages.success(request, f'Загружено: {created_count} создано, {updated_count} обновлено.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            except Exception as e:
                messages.error(request, f'Ошибка при обработке файла: {str(e)}')
    else:
        form = UploadCSVForm()
    return render(request, 'configuration/upload_data.html', {'form': form})
