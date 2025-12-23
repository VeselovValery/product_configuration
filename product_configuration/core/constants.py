# Статусы состояния записей в БД
STATUS_CHOICES = [
    ('active', 'Действующий'),
    ('closed', 'Закрытый')
]
# Запись в БД с отсутствием данных
EMPTY_FILLING = '-пусто-'
# Таблицы для администрирования БД
TABLE_CHOICES = [
    ('BasicPrice', 'Базовый продукт'),
    ('OptionsProfile', 'Данные по опциям'),
    ('OptionsPrice', 'Стоимость опций'),
    ('OptionPartNumber', 'Опциональный продукт'),
]
# Значение НДС
VALUE_ADDED_TAX = 1 + (22 / 100)
