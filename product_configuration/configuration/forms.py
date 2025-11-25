from django import forms

from core.constants import TABLE_CHOICES, OPERATION_CHOICES


class UploadCSVForm(forms.Form):
    table = forms.ChoiceField(
        choices=TABLE_CHOICES,
        label='Таблица БД',
        help_text='Выберите таблицу БД для создания/обновления данных'
    )
    operation = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        label='Операция с БД',
        help_text='Выберите операцию для действия над БД'
    )
    file = forms.FileField(
        label='CSV файл',
        help_text='Выбери CSV файл с данными'
    )
