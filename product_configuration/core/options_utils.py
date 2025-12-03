import re

from typing import Protocol

from configuration.models import OptionsProfile


def replace_count_match(pattern, string, replace, counter):
    def replacer(match):
        replacer.count += 1
        return replace if replacer.count == counter else match.group(0)
    replacer.count = 0
    return re.sub(pattern, replacer, string)


class NamingDevice(Protocol):

    @property
    def slug_type_product(self):
        return str()

    def restructure_name(self, name: str, options: dict):
        pass

    def validate(self, name: str):
        pass


class NsMe:

    def __init__(self, slug_type_product: str):
        self.slug_type_product = slug_type_product

    def restructure_name(self, name: str, options: dict):
        parts_name = [name]
        pattern = r'-[ABCDR]'
        for name_option, value in options.items():
            option = OptionsProfile.objects.get(
                product_type__slug=self.slug_type_product,
                name=name_option
            )
            if option.slug == 'meavr':
                parts_name[0] = replace_count_match(pattern, parts_name[0], '-C', counter=1)
            if option.slug == 'mefloor':
                parts_name[0] = replace_count_match(pattern, parts_name[0], '-C', counter=4)
        return ''.join(parts_name)

    def validate(self, name: str):
        return []


class NsFs:

    def __init__(self, slug_type_product: str):
        self.slug_type_product = slug_type_product

    def restructure_name(self, name: str):
        return name

    def validate(self, name: str):
        return []


class ProcessingDevice:

    def __init__(self, device: NamingDevice):
        self._device = device

    def restructure_name(self, name: str, options: dict):
        return self._device.restructure_name(name, options)

    def validate(self, name: str):
        return self._device.validate(name)


def get_device(device_type: str):
    devices = {
        'nsme': NsMe,
        'nsfs': NsFs
    }
    if device_type not in devices:
        raise ValueError(f'Неизвестный тип продукта: {device_type}')

    cls = devices[device_type]
    return cls(slug_type_product=device_type)