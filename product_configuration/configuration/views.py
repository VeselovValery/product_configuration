import csv
import io
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.generic import ListView

from .forms import UploadCSVForm, ExportCSVForm
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
        product_type = ProductType.objects.get(slug=request.POST.get('product_type'))
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
    type_slug = request.GET.get('type_slug', '')
    if len(query) < 2 or not type_slug:
        return JsonResponse([], safe=False)
    products = BasicPrice.objects.filter(
        name__icontains=query,
        product_type_id=type_slug
    ).values_list('name', flat=True)[:10]
    return JsonResponse(list(products), safe=False)


def get_options(request):
    type_slug = request.GET.get('type_slug')
    if not type_slug:
        return JsonResponse([], safe=False)
    groups_option = list(OptionsGroup.objects.filter(product_type__slug=type_slug))
    if not groups_option:
        return JsonResponse([], safe=False)
    option_names = set()
    for group in groups_option:
        for option in group.options.all():
            option_names.add(option.name)
    descriptions_map = dict(
        OptionsPrice.objects.filter(name__in=option_names).values_list('name', 'description')
    )
    serialized = []
    for group in groups_option:
        # name_list = option.name or []
        name_list = [option.name for option in group.options.all()]
        description_list = [descriptions_map.get(name, '') for name in name_list]
        serialized.append({
            'id': group.id,
            'name': name_list,
            'description': description_list,
            'max_value': group.max_value,
            'value': group.value or [],
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
            file = request.FILES['file']
            model_class = MODEL_MAP.get(table_name)
            if not model_class:
                messages.error(request, 'Неизвестная таблица.')
                return render(request, 'configuration/data_base.html', {'form': form})
            try:
                decoded_file = file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string, delimiter=';')
                rows = list(reader)
                id_list = [row.get('id') for row in rows if row.get('id')]
                existing = {obj.id: obj for obj in model_class.objects.filter(id__in=id_list)}
                lookup_field = 'id'
                created_objects = []
                updated_objects = []
                for row in rows:
                    lookup_value = int(row.get(lookup_field))
                    if 'product_type' in row:
                        product_type_slug = row['product_type'].strip()
                        row['product_type'] = ProductType.objects.get(slug=product_type_slug)
                    if 'values' in row:
                        value_coefficients = row['values']
                        row['values'] = json.loads(value_coefficients) if value_coefficients else []
                    if lookup_value in existing:
                        obj = existing[lookup_value]
                        for field, value in row.items():
                            if field != lookup_field:
                                setattr(obj, field, value)
                        updated_objects.append(obj)
                    else:
                        obj = model_class(**{key: value for key, value in row.items() if key != lookup_field})
                        created_objects.append(obj)
                if created_objects:
                    model_class.objects.bulk_create(created_objects)
                if updated_objects:
                    model_class.objects.bulk_update(updated_objects, [
                        f.name for f in model_class._meta.fields if f.name != lookup_field
                    ], batch_size=1000)
                messages.success(request, f'Создано: {len(created_objects)}, Обновлено: {len(updated_objects)}.')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            except Exception as e:
                messages.error(request, f'Ошибка при обработке файла: {str(e)}')
    else:
        form = UploadCSVForm()
    return render(request, 'configuration/data_base.html', {'form': form})


@login_required(login_url='auth/login/', redirect_field_name='')
def export_data(request):
    if request.method == 'POST':
        form = ExportCSVForm(request.POST)
        if form.is_valid():
            table_name = form.cleaned_data['table']
            model_class = MODEL_MAP.get(table_name)
            if not model_class:
                messages.error(request, 'Неизвестная таблица.')
                return render(request, 'configuration/data_base.html', {'form': form})
            queryset = model_class.objects.all()
            field_names = [f.name for f in model_class._meta.fields]
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{table_name}.csv"'
            response.write('\ufeff')
            writer = csv.writer(response, delimiter=';')
            writer.writerow(field_names)
            for obj in queryset:
                row = []
                for field_name in field_names:
                    if field_name == 'product_type':
                        related_obj = getattr(obj, field_name)
                        value = getattr(related_obj, 'slug', '') if related_obj else ''
                    elif field_name == 'coefficients':
                        value = json.dumps(getattr(obj, field_name))
                    else:
                        value = getattr(obj, field_name)
                    row.append(value)
                writer.writerow(row)
            return response
    else:
        form = ExportCSVForm()
    return render(request, 'configuration/data_base.html', {'form': form})
