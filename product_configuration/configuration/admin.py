from django.contrib import admin

from .models import ProductType, BasicPrice, OptionsPrice, OptionsGroup, Configuration
from core.constants import EMPTY_FILLING


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'slug',
        'name',
        'status'
    )
    list_display_links = ('slug',)
    search_fields = ('slug', 'name')
    list_filter = ('status',)
    empty_value_display = EMPTY_FILLING


@admin.register(BasicPrice)
class BasicPriceAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'product_type',
        'partnumber',
        'price'
    )
    list_display_links = ('name',)
    search_fields = ('name', 'partnumber')
    list_filter = ('product_type', 'status')
    empty_value_display = EMPTY_FILLING


@admin.register(OptionsPrice)
class OptionsPriceAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'product_type',
        'price'
    )
    list_display_links = ('name',)
    search_fields = ('name', 'part_name')
    list_filter = ('product_type', 'status')
    empty_value_display = EMPTY_FILLING


@admin.register(OptionsGroup)
class OptionsGroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'product_type',
        'max_value',
        'value'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('product_type',)
    empty_value_display = EMPTY_FILLING


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'product_type',
        'basic_product',
        'cost'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('product_type', 'basic_product', 'author', 'options')
    empty_value_display = EMPTY_FILLING
