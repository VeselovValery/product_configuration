import re

from typing import Protocol
from django.core.handlers.wsgi import WSGIRequest

from configuration.models import OptionsProfile, BasicPrice



def replace_count_match(pattern, string, replace, counter):
    def replacer(match):
        replacer.count += 1
        return replace if replacer.count == counter else match.group(0)
    replacer.count = 0
    return re.sub(pattern, replacer, string)


class NamingDevice(Protocol):
    request: 'WSGIRequest'
    basic_product: 'BasicPrice'
    value_selected_options: dict

    def get_value_selected_options(self, objects) -> dict:
        ...

    def restructure_name(self, options: dict) -> str:
        ...

    def total_price(self):
        ...

    def validate(self, name: str) -> str:
        ...


class NsMe:

    def __init__(self, request: 'WSGIRequest', basic_product: 'BasicPrice'):
        self.request = request
        self.basic_product = basic_product
        self.value_selected_options = dict()

    def get_value_selected_options(self, objects):
        for key, value in objects.items():
            if key.startswith('option_'):
                parts = key.split('_')
                if len(parts) == 2:
                    if int(value) > 0:
                        try:
                            option_slug = parts[1]
                            self.value_selected_options[option_slug] = int(value)
                        except (ValueError, TypeError):
                            continue
        return self.value_selected_options

    def restructure_name(self, options: dict):
        parts_name = [self.basic_product.name]
        for option_slug, value in options.items():
            if option_slug == 'meavr':
                parts_name[0] = replace_count_match(r'-[ABCDR]', parts_name[0], '-C', counter=1)
            if option_slug == 'mefloor':
                parts_name[0] = replace_count_match(r'-[ABCDR]', parts_name[0], '-C', counter=4)
            if option_slug in ['meaddmas', 'medifsen', 'mecable']:
                if len(parts_name) < 2:
                    parts_name.append('-K0-T2-R-A2-24')
                if option_slug == 'meaddmas':
                    parts_name[1] = replace_count_match(
                        r'(?<=[A-Za-zА-Яа-яЁё])\d-',
                        parts_name[1],
                        f'{2 + value}-',
                        counter=3
                    )
                if option_slug == 'medifsen':
                    parts_name[1] = replace_count_match(r'-[KTRA]', parts_name[1], '-D', counter=4)
                if option_slug == 'mecable':
                    parts_name[1] = replace_count_match(
                        r'(?<=[A-Za-zА-Яа-яЁё])\d-',
                        parts_name[1],
                        f'{value // 5}-',
                        counter=1
                    )
        return ''.join(parts_name)

    def total_price(self):
        pass

    def validate(self, name: str):
        return []


class NsFs:

    def __init__(self, request: 'WSGIRequest', basic_product: 'BasicPrice'):
        self.request = request
        self.basic_product = basic_product
        self.value_selected_options = dict()

    def restructure_name(self, options: dict):
        pass

    def validate(self, name: str):
        pass


class ProcessingDevice:

    def __init__(self, device: NamingDevice):
        self._device = device

    def get_value_selected_options(self, objects):
        return self._device.get_value_selected_options(objects)

    def restructure_name(self, options: dict):
        return self._device.restructure_name(options)

    def validate(self, name: str):
        return self._device.validate(name)


def get_device(request, basic_product):
    devices = {
        'nsme': NsMe,
        'nsfs': NsFs
    }
    device_type = basic_product.product_type.slug
    if device_type not in devices:
        raise ValueError(f'Неизвестный тип продукта: {device_type}')
    cls = devices[device_type]
    return cls(request=request, basic_product=basic_product)
