# Статусы состояния записей в БД
STATUS_CHOICES = [
    ('active', 'Действующий'),
    ('closed', 'Закрытый')
]
# Запись в БД с отсутствием данных
EMPTY_FILLING = '-пусто-'
# Таблицы для загрузки в БД
TABLE_INPUT = [
    ('BasicPrice', 'Базовый продукт'),
    ('OptionsProfile', 'Данные по опциям'),
    ('OptionsPrice', 'Стоимость опций'),
    ('OptionPartNumber', 'Опциональный продукт'),
]
# Таблицы для выгрузки из БД
TABLE_OUTPUT = [
    ('BasicPrice', 'Базовый продукт'),
    ('OptionsProfile', 'Данные по опциям'),
    ('OptionsPrice', 'Стоимость опций'),
    # ('OptionPartNumber', 'Опциональный продукт'),
    ('Configuration', 'Расчеты')
]
# Значение НДС
VALUE_ADDED_TAX = 1 + (22 / 100)
