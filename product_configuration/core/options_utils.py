import re

from typing import Protocol
from functools import cached_property
from django.core.handlers.wsgi import WSGIRequest

from configuration.models import BasicPrice, OptionsProfile, OptionsPrice


def replace_count_match(pattern, string, replace, counter):
    def replacer(match):
        replacer.count += 1
        return replace if replacer.count == counter else match.group(0)
    replacer.count = 0
    return re.sub(pattern, replacer, string)


class NamingDevice(Protocol):
    request: 'WSGIRequest'
    basic_product: 'BasicPrice'
    parts_full_name: list
    properties: dict

    @cached_property
    def value_selected_options(self) -> dict:
        ...

    @cached_property
    def full_name(self) -> str:
        ...

    @cached_property
    def total_price(self) -> int:
        ...

    def update_data(self, options: dict, value: int):
        ...

    def get_option_price(self, option_slug: str) -> 'OptionsPrice':
        ...


class Device:

    def __init__(self, request: 'WSGIRequest'):
        self.request = request
        self.basic_product = BasicPrice.objects.get(name=request.POST.get('base_name'))
        self.parts_full_name = [self.basic_product.name]
        self.properties = dict()

    @cached_property
    def value_selected_options(self) -> dict:
        value_selected_options = {}
        for key, value in self.request.POST.items():
            if key.startswith('option_'):
                parts = key.split('_')
                if len(parts) == 2:
                    if value != '0':
                        try:
                            option_slug = parts[1]
                            value_selected_options[option_slug] = value
                            self.update_data(option_slug, value)
                        except (ValueError, TypeError):
                            continue
        return value_selected_options

    @cached_property
    def full_name(self):
        return ''.join(self.parts_full_name)

    def update_data(self, option_slug: str, value: str):
        pass

    def get_option_price(self, option_slug: str):
        variant = getattr(self.basic_product, option_slug, 1)
        return OptionsPrice.objects.get(option__slug=option_slug, variant=variant)


class NsMe(Device):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)

    @cached_property
    def total_price(self):
        total_price = self.basic_product.price
        for option_slug, value in self.value_selected_options.items():
            if option_slug == 'medifsen':
                option_price = self.get_option_price(option_slug)
                total_price += (self.properties.get('master_pumps', 2) * option_price.price)
            elif option_slug == 'mecable':
                option_price = self.get_option_price(option_slug)
                total_price += (getattr(self.basic_product, 'value_pupms', 1) * option_price.price * int(value))
            else:
                option_price = self.get_option_price(option_slug)
                total_price += (option_price.price * int(value))
        return total_price

    def update_data(self, option_slug: str, value: str):
        """
            Обновление свойств self.parts_full_name и self.properties.
        """
        if option_slug == 'meavr':
            self.parts_full_name[0] = replace_count_match(r'-[ABCDR]', self.parts_full_name[0], '-C', counter=1)
        if option_slug == 'mefloor':
            self.parts_full_name[0] = replace_count_match(r'-[ABCDR]', self.parts_full_name[0], '-C', counter=4)
        if option_slug in ['meaddmas', 'medifsen', 'mecable']:
            if len(self.parts_full_name) < 2:
                self.parts_full_name.append('-K0-T2-R-A2-24')
            if option_slug == 'meaddmas':
                self.parts_full_name[1] = replace_count_match(
                    r'(?<=[A-Za-zА-Яа-яЁё])\d-',
                    self.parts_full_name[1],
                    f'{2 + int(value)}-',
                    counter=3
                )
                self.properties['master_pumps'] = value + 2
            if option_slug == 'medifsen':
                self.parts_full_name[1] = replace_count_match(r'-[KTRA]', self.parts_full_name[1], '-D', counter=4)
            if option_slug == 'mecable':
                self.parts_full_name[1] = replace_count_match(
                    r'(?<=[A-Za-zА-Яа-яЁё])\d-',
                    self.parts_full_name[1],
                    f'{int(value) // 5}-',
                    counter=1
                )


class NsFs(Device):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)

    @cached_property
    def total_price(self):
        pass

    def update_data(self, option_slug: str, value: str):
        pass


class ProcessingDevice:

    def __init__(self, device: NamingDevice):
        self._device = device

    @cached_property
    def basic_product(self):
        return self._device.basic_product

    @cached_property
    def value_selected_options(self):
        return self._device.value_selected_options

    @cached_property
    def full_name(self):
        return self._device.full_name

    @cached_property
    def total_price(self):
        return self._device.total_price


def get_device(request):
    devices = {
        'nsme': NsMe,
        'nsfs': NsFs
    }
    device_type = request.POST.get('product_type')
    if device_type not in devices:
        raise ValueError(f'Неизвестный тип продукта: {device_type}')
    cls = devices[device_type]
    return cls(request=request)
