from django import forms

from core.constants import TABLE_INPUT, TABLE_OUTPUT


class UploadCSVForm(forms.Form):
    table = forms.ChoiceField(
        choices=TABLE_INPUT,
        label='Таблица БД',
        help_text='Выберите таблицу БД для обновления данных'
    )
    file = forms.FileField(
        label='CSV файл',
        help_text='Выбери CSV файл с данными',
        widget=forms.ClearableFileInput(attrs={'accept': '.csv'})
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        if uploaded_file:
            filename = uploaded_file.name.lower()
            if not filename.endswith('.csv'):
                raise forms.ValidationError('Разрешены только файлы с расширением .csv')
        return uploaded_file


class ExportCSVForm(forms.Form):
    table = forms.ChoiceField(
        choices=TABLE_OUTPUT,
        label='Таблица БД',
        help_text='Выберите таблицу БД для выгрузки данных'
    )
