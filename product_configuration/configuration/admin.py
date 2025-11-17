from django.contrib import admin

from .models import ProductType, BasicPrice, OptionsPrice, Configuration
from core.constants import EMPTY_FILLING


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'slug',
        'title',
        'status'
    )
    list_display_links = ('slug',)
    search_fields = ('slug', 'title')
    list_filter = ('status',)
    empty_value_display = EMPTY_FILLING


@admin.register(BasicPrice)
class BasicPriceAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'product_type',
        'partnumber',
        'price'
    )
    list_display_links = ('title',)
    search_fields = ('title', 'partnumber')
    list_filter = ('product_type', 'status')
    empty_value_display = EMPTY_FILLING


@admin.register(OptionsPrice)
class OptionsPriceAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'product_type',
        'price'
    )
    list_display_links = ('title',)
    search_fields = ('title', 'part_name')
    list_filter = ('product_type', 'status')
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
