import csv
import io
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.generic import ListView

from .forms import UploadCSVForm, ExportCSVForm
from .models import ProductType, BasicPrice, OptionsProfile, OptionsPrice, Configuration, OptionPartNumber
from core.constants import STATUS_CHOICES, VALUE_ADDED_TAX

from core.options_utils import get_device, ProcessingDevice
from core.errors import OptionDoesNotExist, OptionConstraintWorked, PumpsDoesNotFind


# Таблицы для загрузки и выгрузки
MODEL_MAP = {
    'BasicPrice': BasicPrice,
    'OptionsProfile': OptionsProfile,
    'OptionsPrice': OptionsPrice,
    'OptionPartNumber': OptionPartNumber,
    'Configuration': Configuration
}
# Таблица замены похожих русских букв на английские для поиска
RUS_TO_LAT_TRANSLATION = str.maketrans({
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
    'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X',
    'а': 'a', 'в': 'b', 'е': 'e', 'к': 'k', 'м': 'm', 'н': 'h',
    'о': 'o', 'р': 'p', 'с': 'c', 'т': 't', 'у': 'y', 'х': 'x',
})
# Группировка типов продуктов для вывода опций по нескольким группам продукта
GROUP_TYPE_PRODUCT = {
    'hydrompc': ['hydrompc', 'shutpmpcv'],
    'nsfs': ['nsfs', 'shupnfs'],
    'bme': ['bme', 'bm'],
    'boe': ['boe', 'bo'],
    'kmge': ['kmge', 'kmg']
}


def normalize_for_search(text: str) -> str:
    """Нормализует строку для поиска:
    - заменяет похожие русские буквы на английские
    - приводит к нижнему регистру
    """
    if not text:
        return ''
    return text.translate(RUS_TO_LAT_TRANSLATION).lower()


def normalize_status(raw_status: str) -> str:
    """Приводит строку статуса из CSV к валидному коду из STATUS_CHOICES.
    Если значение пустое или не распознано, возвращает 'active'.
    """
    if raw_status is None:
        return 'active'
    raw = raw_status.strip()
    if not raw:
        return 'active'
    # Словари для поиска по коду и по отображаемому значению
    code_by_code = {code.lower(): code for code, _ in STATUS_CHOICES}
    code_by_label = {label.lower(): code for code, label in STATUS_CHOICES}
    lower = raw.lower()
    # Если пришёл уже корректный код ('active' / 'closed')
    if lower in code_by_code:
        return code_by_code[lower]
    # Если пришло отображаемое значение ('Действующий' / 'Закрытый')
    if lower in code_by_label:
        return code_by_label[lower]
    # Фоллбек по умолчанию
    return 'active'


@login_required(login_url='auth/login/', redirect_field_name='')
def index(request):
    if request.method == 'POST':
        device = get_device(request)
        processor = ProcessingDevice(device)
        basic_product = processor.basic_product
        try:
            if processor.validate_constraints:
                total_price = processor.total_price  # Цена конечного продукта с опциями без НДС
                total_price_vat = total_price * VALUE_ADDED_TAX if type(total_price) is int else 'по запросу'
                # Формирование наименования опционального изделия
                full_name = processor.full_name
                # Запись данных о расчете
                config = Configuration.objects.create(
                    product_type=basic_product.product_type,
                    basic_product=basic_product,
                    name=full_name,
                    cost_without_vat=total_price,
                    cost_with_vat=total_price_vat,
                    author=request.user,
                )
                selected_options = [OptionsProfile.objects.get(slug=slug) for slug, value in processor.value_selected_options.items()]
                config.options.set(selected_options)
                config.options_value = [
                    f'* {option.name} - {processor.value_selected_options[option.slug]}' for option in selected_options
                ]
                config.save()
                if full_name != basic_product.name:
                    options_device, created_options_device = OptionPartNumber.objects.get_or_create(
                        name=full_name,
                        defaults={
                            'name': full_name,
                            'part_number': 'по запросу'
                        }
                    )
                    part_number = 'по запросу' if created_options_device else options_device.part_number
                else:
                    part_number = basic_product.part_number
                # Возврат названия и цены продукции
                return JsonResponse({
                    'full_name': full_name,
                    'part_number': part_number,
                    'total_price': total_price,
                    'total_price_vat': total_price_vat,
                })
        except (OptionConstraintWorked, OptionDoesNotExist, PumpsDoesNotFind) as error:
            return JsonResponse({'error': str(error)}, status=400)
    else:
        types = ProductType.objects.filter(status='active')
        return render(request, 'configuration/index.html', {'product_types': types})


@login_required(login_url='auth/login/', redirect_field_name='')
def validate_options(request):
    """Промежуточная валидация ограничений опций без сохранения конфигурации."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST'}, status=405)
    try:
        base_name = (request.POST.get('base_name') or '').strip()
        if not base_name:
            return JsonResponse({'error': 'Не выбрано наименование базового продукта'}, status=400)
        device = get_device(request)
        processor = ProcessingDevice(device)
        if processor.validate_constraints:
            return JsonResponse({'ok': True})
    except (OptionConstraintWorked, OptionDoesNotExist) as error:
        return JsonResponse({'error': str(error)}, status=400)
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=400)
    return JsonResponse({'ok': True})


def autocomplete_base_products(request):
    query = request.GET.get('q', '')
    type_slug = request.GET.get('type_slug', '')
    if len(query) < 2 or not type_slug:
        return JsonResponse([], safe=False)
    products = BasicPrice.objects.filter(
        product_type_id=type_slug
    ).values_list('name', flat=True)[:200]
    norm_query = normalize_for_search(query)
    matched = []
    for name in products:
        if norm_query in normalize_for_search(name):
            matched.append(name)
        if len(matched) >= 10:
            break
    return JsonResponse(matched, safe=False)


def get_options(request):
    type_slug = request.GET.get('type_slug')
    if not type_slug:
        return JsonResponse([], safe=False)
    type_slug = GROUP_TYPE_PRODUCT.get(type_slug, [type_slug])
    options = list(
        OptionsProfile.objects.filter(
            product_type__slug__in=type_slug,
            status='active'
        )
    )
    if not options:
        return JsonResponse([], safe=False)
    serialized = [
        {
            'id': option.id,
            'slug': option.slug,
            'name': option.name,
            'description': option.description,
            'value': option.values or [],
        }
        for option in options
    ]
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
                if model_class is OptionPartNumber:
                    model_class.objects.all().delete()
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
                        product_type_slug = (row['product_type'] or '').strip()
                        row['product_type'] = ProductType.objects.get(slug=product_type_slug)
                    if 'option' in row:
                        option_slug = (row['option'] or '').strip()
                        row['option'] = OptionsProfile.objects.get(slug=option_slug)
                    if 'values' in row:
                        values = (row['values'] or []).strip()
                        row['values'] = json.loads(values) if values else []
                    if 'options_value' in row:
                        values = (row['options_value'] or []).strip()
                        row['options_value'] = json.loads(values) if values else []
                    if 'status' in row:
                        row['status'] = normalize_status(row.get('status'))
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
                    if field_name in ['product_type', 'option']:
                        related_obj = getattr(obj, field_name)
                        value = getattr(related_obj, 'slug', '') if related_obj else ''
                    elif field_name in ['values', 'options_value']:
                        value = json.dumps(getattr(obj, field_name), ensure_ascii=False)
                    else:
                        value = getattr(obj, field_name)
                    row.append(value)
                writer.writerow(row)
            return response
    else:
        form = ExportCSVForm()
    return render(request, 'configuration/data_base.html', {'form': form})
