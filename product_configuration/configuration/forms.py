from django import forms
from .models import ProductType


class BasicConfigForm(forms.Form):
    product_type = forms.ModelChoiceField(
        queryset=ProductType.objects.filter(status='active'),
        label='Тип продукта'
    )
    base_name = forms.CharField(
        max_length=256,
        label='Наименование базовой версии продукта',
        widget=forms.TextInput(attrs={'placeholder': 'Введите наименование базовой версии продукта'})
    )
