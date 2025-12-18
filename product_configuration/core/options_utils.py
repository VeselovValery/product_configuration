import re

from typing import Protocol
from functools import cached_property
from django.core.handlers.wsgi import WSGIRequest

from configuration.models import BasicPrice, OptionsProfile, OptionsPrice, OptionsConstraint

from .errors import OptionDoesNotExist, OptionConstraintWorked

# Таблица с заменой обозначения тока жокей насоса
REPLACE_CURRENT_JOCKEY = {
    '0,63-1': '2',
    '1-1,6': '3',
    '1,6-2,5': '4',
    '2,5-4': '5',
    '4-6': '6',
    '6-9': '7',
    '9-14': '8'
}


def replace_count_match(pattern, string, replace, counter):
    def replacer(match):
        replacer.count += 1
        return replace if replacer.count == counter else match.group(0)
    replacer.count = 0
    return re.sub(pattern, replacer, string)


def search_fragment(pattern, text):
    match = re.search(pattern, text)
    if match:
        return match.groups()


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

    @cached_property
    def validate_constraints(self) -> bool:
        ...

    def update_data(self, options: dict, value: int):
        ...

    def get_option_price(self, option_slug: str) -> 'OptionsPrice':
        ...


class Device:

    def __init__(self, request: 'WSGIRequest'):
        self.request = request
        self.basic_product = BasicPrice.objects.get(name=request.POST.get('base_name'))
        self.product_type = self.basic_product.product_type
        self.parts_full_name = [self.basic_product.name, '', '']

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

    @cached_property
    def validate_constraints(self):
        constraints = OptionsConstraint.objects.filter(product_type__slug=self.product_type.slug)
        for constraint in constraints.prefetch_related('options'):
            related_slugs = {option.slug for option in constraint.options.all()}
            if constraint.max_total_value == 0:
                selected_slug = {slug for slug, value in self.value_selected_options.items() if slug in related_slugs}
                if selected_slug == related_slugs:
                    raise OptionConstraintWorked(constraint.title)
            else:
                total = sum(int(value) for slug, value in self.value_selected_options.items() if slug in related_slugs)
                if total > constraint.max_total_value:
                    raise OptionConstraintWorked(constraint.title)
        return True

    def update_data(self, option_slug: str, value: str):
        pass

    def get_option_price(self, option_slug: str):
        try:
            variant = getattr(self.basic_product, option_slug, 1)
            return OptionsPrice.objects.get(option__slug=option_slug, variant=variant)
        except OptionsPrice.DoesNotExist:
            raise OptionDoesNotExist(option_slug)


class DeviceME(Device):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)
        self.properties = {'master_pumps': 2}

    @cached_property
    def total_price(self):
        total_price = self.basic_product.price
        for option_slug, value in self.value_selected_options.items():
            try:
                option_price = self.get_option_price(option_slug)
                if option_slug == 'medifsen':
                    total_price += (self.properties.get('master_pumps', 2) * option_price.price)
                elif option_slug == 'mecable':
                    total_price += (getattr(self.basic_product, 'value_pumps', 1) * option_price.price * int(value))
                else:
                    total_price += (option_price.price * int(value))
            except OptionDoesNotExist:
                raise
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
            if not self.parts_full_name[1]:
                self.parts_full_name[1] = '-K0-T2-R-A2-24'
            if option_slug == 'meaddmas':
                self.parts_full_name[1] = replace_count_match(
                    r'(?<=[A-Za-zА-Яа-яЁё])\d-',
                    self.parts_full_name[1],
                    f'{2 + int(value)}-',
                    counter=3
                )
                self.properties['master_pumps'] += int(value)
            if option_slug == 'medifsen':
                self.parts_full_name[1] = replace_count_match(r'-[KTRA]', self.parts_full_name[1], '-D', counter=4)
            if option_slug == 'mecable':
                self.parts_full_name[1] = replace_count_match(
                    r'(?<=[A-Za-zА-Яа-яЁё])\d-',
                    self.parts_full_name[1],
                    f'{int(value) // 5}-',
                    counter=1
                )


class DeviceFS(Device):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)
        self.properties = {'valves': 1}

    @cached_property
    def total_price(self):
        total_price = self.basic_product.price
        main_pumps = getattr(self.basic_product, 'main_pumps', 1)
        reserve_pumps = getattr(self.basic_product, 'reserve_pumps', 1)
        for option_slug, value in self.value_selected_options.items():
            try:
                option_price = self.get_option_price(option_slug)
                if option_slug == 'fsupcurrent':
                    total_price += (self.properties.get('valves', 1) * int(value) * option_price.price)
                elif option_slug == 'softstarter':
                    value_soft_starter = main_pumps if value == 'Основные насосы' else main_pumps + reserve_pumps
                    total_price += (value_soft_starter * option_price.price)
                elif option_slug == 'fscable':
                    total_price += ((main_pumps + reserve_pumps) * option_price.price * int(value))
                elif option_slug == 'fsjockey':
                    total_price += option_price.price
                else:
                    total_price += (option_price.price * int(value))
            except OptionDoesNotExist:
                raise
        return total_price

    def update_data(self, option_slug: str, value: str):
        """
            Обновление свойств self.parts_full_name и self.properties.
        """
        if option_slug == 'fsjockey':
            if value != getattr(self.basic_product, 'current_jockey', '0,63-1'):
                if not self.parts_full_name[1]:
                    self.parts_full_name[1] = '-S0T1000000000'
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9]',
                    self.parts_full_name[1],
                    REPLACE_CURRENT_JOCKEY.get(value, '0'),
                    counter=9
                )
        elif option_slug == 'fscable':
            if not self.parts_full_name[2]:
                self.parts_full_name[2] = '-K000000'
            self.parts_full_name[2] = replace_count_match(
                r'[A-Z0-9]',
                self.parts_full_name[2],
                f'{int(value) // 5}',
                counter=2
            )
        else:
            if not self.parts_full_name[1]:
                self.parts_full_name[1] = '-S0T1000000000'
            matches_valves = re.findall(r'[ST](\d)', self.parts_full_name[1])
            digit_after_s = int(matches_valves[0])
            digit_after_t = int(matches_valves[1])
            if option_slug == 'volbasevalve':
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9]',
                    self.parts_full_name[1],
                    str(digit_after_s + 1),
                    counter=2
                )
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9]',
                    self.parts_full_name[1],
                    str(digit_after_t - 1),
                    counter=4
                )
            if option_slug in ['fs1phvalve', 'fs3phvalve']:
                replace = digit_after_s + int(value) if option_slug == 'fs1phvalve' else digit_after_t + int(value)
                counter = 2 if option_slug == 'fs1phvalve' else 4
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9]',
                    self.parts_full_name[1],
                    str(replace),
                    counter=counter
                )
                self.properties['valves'] += int(value)
            if option_slug == 'fsupcurrent':
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9]',
                    self.parts_full_name[1],
                    value,
                    counter=8
                )
            if option_slug in ['fsdrainagefloat', 'fsdrainage']:
                replace = f'D{value}' if option_slug == 'fsdrainagefloat' else f'P{value}'
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9][A-Z0-9]',
                    self.parts_full_name[1],
                    replace,
                    counter=3
                )
            if option_slug in ['colorcabinet', 'noneutral']:
                matches_execution = re.findall(r'[A-Z0-9]', self.parts_full_name[1])
                digit_execution = int(matches_execution[9])
                replace = digit_execution + 1 if option_slug == 'colorcabinet' else digit_execution + 2
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9]',
                    self.parts_full_name[1],
                    str(replace),
                    counter=10
                )
            if option_slug == 'softstarter':
                replace = 'M' if value == 'Основные насосы' else 'A'
                self.parts_full_name[1] = replace_count_match(
                    r'[A-Z0-9]',
                    self.parts_full_name[1],
                    replace,
                    counter=7
                )


class DeviceMPC(Device):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)
        self.properties = {'inputs': 1}
        self.option_part_name_1 = []
        self.option_part_name_2 = []
        self.parts_full_name = [self.basic_product.name]
        self.dispatching = {
            'mpcmodbus': [1, '1'],
            'mpcgsm': [2, '2'],
            'mpcfcdoor': [3, '3'],
            'mpc16di': [4, '4'],
            'mpc16do': [5, '5'],
            'mpc8ai': [6, '6'],
            'mpc8ao': [7, '7']
        }
        self.mpc_bypass = {'DOL': '-B1', 'SD': '-B2', 'SS': '-B3'}
        self.mpc_filter = {'du/dt': '-UT', 'Синусоидальный': '-SW'}
        self.input_protection = {'mpctransient': [1, 'T'], 'mpclightning': [1, 'L'], 'mpcphase': [2, 'P']}
        self.pump_protection = {
            'mpcelectrode': [1, 'DR'],
            'mpcpt': [2, ''],
            'mpcprotection': [3, 'MP'],
            'mpcbattery': [4, 'AB']
        }
        self.indication = {
            'mpcammeter': [1, 'A'],
            'mpcvoltmeter': [2, 'V'],
            'mpcisupply': [3, 'L1'],
            'mpcialarm': [4, 'L2'],
            'mpciwork': [5, 'L3'],
            'mpcipumpwork': [6, 'L4'],
            'mpchourmeter': [7, 'C1'],
            'mpcstartmeter': [8, 'C2'],
            'mpcsiren': [9, 'S'],
            'mpcflashing': [10, 'F1'],
            'mpcextflashing': [11, 'F2']
        }
        self.dry_run_protection = {'Реле': '-R', 'Датчик': '-S'}
        self.out_sensor = {
            'Датчик (1ОС)': '-A1',
            'Датчик (1ОС+1РЕЗ)': '-A2',
            'Диф.Датчик (1ОС)': '-D1',
            'Диф.Датчик (1ОС+1РЕЗ)': '-D2'
        }

    @cached_property
    def total_price(self):
        total_price = self.basic_product.price
        value_pumps = getattr(self.basic_product, 'value_pumps', 1)
        neutral = getattr(self.basic_product, 'neutral', 1)
        for option_slug, value in self.value_selected_options.items():
            try:
                option_price = self.get_option_price(option_slug)
                if option_slug in ['mpctransient', 'mpclightning']:
                    total_price += ((self.properties.get('inputs', 1) + neutral) * option_price.price)
                elif option_slug == 'mpcvoltmeter':
                    total_price += (self.properties.get('inputs', 1) * option_price.price)
                elif option_slug == 'mpcammeter':
                    total_price += (value_pumps * option_price.price)
                elif option_slug == 'mpccable':
                    total_price += (value_pumps * option_price.price * int(value))
                elif option_slug in ['mpcdryprotec', 'mpcoutsensor', 'mpcbypass', 'mpcfilter']:
                    if value not in ['Реле', 'Датчик (1ОС)']:
                        total_price += option_price.price
                else:
                    total_price += (option_price.price * int(value))
            except OptionDoesNotExist:
                raise
        return total_price

    @cached_property
    def full_name(self):
        option_name_1 = []
        for item in self.option_part_name_1:
            option_name_1.extend(item) if isinstance(item, list) else option_name_1.append(item)
        self.parts_full_name.append(''.join(option_name_1))
        self.parts_full_name.append(''.join(self.option_part_name_2))
        return ''.join(self.parts_full_name)

    def update_data(self, option_slug: str, value: str):
        if option_slug == 'mpcavr':
            self.parts_full_name[0] = self.option_avr()
            self.properties['inputs'] = 2
        elif option_slug in ['mpccable', 'mpcdryprotec', 'mpcoutsensor'] and value not in ['Реле', 'Датчик (1ОС)']:
            if not self.option_part_name_2:
                self.option_part_name_2 = ['-K0', '-T2', '-R', '-A1', '-24']
            if option_slug == 'mpccable':
                self.option_part_name_2[0] = f'-K{int(value) // 5}'
            elif option_slug == 'mpcdryprotec':
                self.option_part_name_2[2] = self.dry_run_protection[value]
            elif option_slug == 'mpcoutsensor':
                self.option_part_name_2[3] = self.out_sensor[value]
        else:
            if not self.option_part_name_1:
                self.option_part_name_1 = [
                    [''] * 8,
                    '',
                    '',
                    [''] * 3,
                    [''] * 5,
                    [''] * 12
                ]
            if option_slug in self.dispatching.keys():
                self.option_part_name_1[0][0] = '-D'
                option = self.dispatching[option_slug]
                self.option_part_name_1[0][option[0]] = option[1]
            elif option_slug == 'mpcbypass':
                self.option_part_name_1[1] = self.mpc_bypass[value]
            elif option_slug == 'mpcfilter':
                self.option_part_name_1[2] = self.mpc_filter[value]
            elif option_slug in self.input_protection.keys():
                self.option_part_name_1[3][0] = '-'
                option = self.input_protection[option_slug]
                self.option_part_name_1[3][option[0]] = option[1]
            elif option_slug in self.pump_protection.keys():
                self.option_part_name_1[4][0] = '-'
                option = self.pump_protection[option_slug]
                if option_slug == 'mpcpt':
                    self.option_part_name_1[4][option[0]] = f'P{value}'
                else:
                    self.option_part_name_1[4][option[0]] = option[1]
            elif option_slug in self.indication.keys():
                self.option_part_name_1[5][0] = '-'
                option = self.indication[option_slug]
                self.option_part_name_1[5][option[0]] = option[1]

    def option_avr(self):
        return replace_count_match(r'-[ABC]', self.parts_full_name[0], '-D', counter=1)


class CabinetMPC(DeviceMPC):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)

    def option_avr(self):
        match = re.search(r'-FC', self.parts_full_name[0])
        if match:
            position = match.end()
            return self.parts_full_name[0][:position] + "-АВР" + self.parts_full_name[0][position:]
        return self.parts_full_name[0]


class PumpBM(Device):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)

    @cached_property
    def validate_constraints(self):
        try:
            if super().validate_constraints:
                if self.product_type.slug == 'bme':
                    pump = search_fragment(r'(BME|BMNE)(\s+)([0-9]+)(?=-)', self.basic_product.name)
                    if 'bmsensor' in self.value_selected_options:
                        if pump[0] == 'BMNE':
                            if int(pump[2]) in range(1, 21):
                                raise OptionConstraintWorked(
                                    'Опция Датчик давления не совместима с насосами серии BMNE1...BMNE20'
                                )
                return True
        except OptionConstraintWorked:
            raise

    @cached_property
    def total_price(self):
        total_price = self.basic_product.price
        for option_slug, value in self.value_selected_options.items():
            try:
                option_price = self.get_option_price(option_slug)
                if value != 'EPDM':
                    total_price += option_price.price
            except OptionDoesNotExist:
                raise
        return total_price

    def update_data(self, option_slug: str, value: str):
        if option_slug in ['bmautomat', 'bmsensor', 'bmptcoff']:
            execution_code = search_fragment(r'(?<= )([A-Z]+)(?=-)', self.parts_full_name[0])[0]
            if execution_code:
                if option_slug == 'bmautomat':
                    execution_code_parts = [letter for letter in execution_code if letter in ['S', 'N']]
                    execution_code_parts.append('O')
                    execution_code_parts.sort(reverse=True)
                elif option_slug == 'bmsensor':
                    execution_code_parts = [letter for letter in execution_code if letter in ['S', 'R', 'O']]
                    execution_code_parts.append('N')
                elif option_slug == 'bmptcoff':
                    execution_code_parts = [letter for letter in execution_code if letter in ['S', 'N']]
                    execution_code_parts.insert(0, 'A')
                self.parts_full_name[0] = re.sub(
                    r'(?<= )([A-Z]+)(?=-)',
                    ''.join(execution_code_parts),
                    self.parts_full_name[0]
                )
        elif option_slug == 'bmelastomer':
            replace = 'E' if value == 'EPDM' else 'V'
            self.parts_full_name[0] = re.sub(r'(?<=-)[EV](?=-)', replace, self.parts_full_name[0])
            self.parts_full_name[0] = re.sub(r'[EV]$', replace, self.parts_full_name[0])


class PumpBO(Device):

    def __init__(self, request: 'WSGIRequest'):
        super().__init__(request)

    def update_data(self, option_slug: str, value: str):
        if option_slug in ['boautomat', 'bosensor', 'bodifsensor']:
            execution_code = search_fragment(r'(?<= )([A-Z]+)(?=-)', self.parts_full_name[0])[0]
            execution_code_parts = [letter for letter in execution_code]
            if execution_code:
                if option_slug == 'boautomat':
                    execution_code_parts[0] = 'O'
                elif option_slug == 'bosensor':
                    execution_code_parts[1] = 'N'
                elif option_slug == 'bodifsensor':
                    execution_code_parts[1] = 'D'
                self.parts_full_name[0] = re.sub(
                    r'(?<= )([A-Z]+)(?=-)',
                    ''.join(execution_code_parts),
                    self.parts_full_name[0]
                )


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
        try:
            return self._device.total_price
        except OptionDoesNotExist:
            raise

    @cached_property
    def validate_constraints(self):
        try:
            return self._device.validate_constraints
        except OptionConstraintWorked:
            raise


def get_device(request):
    devices = {
        'nsme': DeviceME,
        'nsfs': DeviceFS,
        'shupnfs': DeviceFS,
        'hydrompc': DeviceMPC,
        'shutpmpcv': CabinetMPC,
        'bm': PumpBM,
        'bme': PumpBM
    }
    device_type = request.POST.get('product_type')
    if device_type not in devices:
        raise ValueError(f'Неизвестный тип продукта: {device_type}')
    cls = devices[device_type]
    return cls(request=request)
