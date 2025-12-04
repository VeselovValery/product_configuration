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
from django.core.exceptions import ValidationError

from .forms import UploadCSVForm, ExportCSVForm
from .models import ProductType, BasicPrice, OptionsProfile, OptionsPrice, Configuration, \
    OptionsConstraint  # OptionsGroup,
from core.constants import STATUS_CHOICES

from core.options_utils import get_device, ProcessingDevice

# Таблицы для загрузки и выгрузки
MODEL_MAP = {
    'BasicPrice': BasicPrice,
    'OptionsProfile': OptionsProfile,
    'OptionsPrice': OptionsPrice
}
# Таблица замены похожих русских букв на английские для поиска
RUS_TO_LAT_TRANSLATION = str.maketrans({
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
    'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X',
    'а': 'a', 'в': 'b', 'е': 'e', 'к': 'k', 'м': 'm', 'н': 'h',
    'о': 'o', 'р': 'p', 'с': 'c', 'т': 't', 'у': 'y', 'х': 'x',
})


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


def validate_constraints(product_type, option_values):
    # option_values: dict[slug] -> int
    constraints = OptionsConstraint.objects.filter(product_type=product_type)
    for constraint in constraints.prefetch_related('options'):
        related_slugs = {opt.slug for opt in constraint.options.all()}
        total = sum(value for slug, value in option_values.items() if slug in related_slugs)
        if total > constraint.max_total_value:
            raise ValidationError(
                f'Суммарный объём для {constraint.title} не может быть больше {constraint.max_total_value}.'
            )


@login_required(login_url='auth/login/', redirect_field_name='')
def index(request):
    if request.method == 'POST':
        print(request.POST.get('product_type'))
        product_type = ProductType.objects.get(slug=request.POST.get('product_type'))
        basic_product = BasicPrice.objects.get(name=request.POST.get('base_name'))
        device = get_device(request, basic_product)
        processor = ProcessingDevice(device)
        # Обработка опций: каждая опция представлена одним select-элементом
        # с именем вида "option_<slug_опции>" и значением – выбранным объемом.

        value_selected_options = processor.get_value_selected_options(request.POST)
        # value_selected_options = {}
        # for key, value in request.POST.items():
        #     if key.startswith('option_'):
        #         parts = key.split('_')
        #         if len(parts) == 2:
        #             if int(value) > 0:
        #                 try:
        #                     option_slug = parts[1]
        #                     value_selected_options[option_slug] = int(value)
        #                 except (ValueError, TypeError):
        #                     continue
        total_price = basic_product.price  # Цена конечного продукта с опциями
        # Получаем стоимость опции из OptionsPrice и умножаем на выбранный объем
        # variant = getattr(option, option_slug, 1)
        # option_price = OptionsPrice.objects.get(option=option, variant=variant)
        # total_price += (option_price.price * value)
        # Формирование наименования опционального изделия
        full_name = processor.restructure_name(value_selected_options)
        # Запись данных о расчете
        config = Configuration.objects.create(
            product_type=product_type,
            basic_product=basic_product,
            name=full_name,
            cost=total_price,
            author=request.user,
        )
        selected_options = [OptionsProfile.objects.get(slug=slug) for slug, value in value_selected_options.items()]
        config.options.set(selected_options)
        config.options_value = [
            f'* {option.name} - {value_selected_options[option.slug]}' for option in selected_options
        ]
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
    # Получаем все продукты для заданного типа (ограничиваем количество для производительности)
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
    # Все опции теперь берутся напрямую из OptionsProfile без группировки
    options = list(
        OptionsProfile.objects.filter(
            product_type__slug=type_slug,
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
            # Массив возможных значений объемов подключения опции
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
                        value_coefficients = (row['values'] or []).strip()
                        row['values'] = json.loads(value_coefficients) if value_coefficients else []
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
