from django.contrib import admin

from .models import ProductType, BasicPrice, OptionsProfile, OptionsPrice, OptionsCoef, Configuration  #OptionsGroup,
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


@admin.register(OptionsProfile)
class OptionsProfileAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'slug',
        'name',
        'product_type',
    )
    list_display_links = ('name',)
    search_fields = ('slug', 'name',)
    list_filter = ('product_type', 'status')
    empty_value_display = EMPTY_FILLING


@admin.register(OptionsCoef)
class OptionsCoefAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'product_type',
        'option',
        'name_coef'
    )
    list_display_links = ('title',)
    search_fields = ('title',)
    list_filter = ('product_type', 'option')
    empty_value_display = EMPTY_FILLING


# @admin.register(OptionsGroup)
# class OptionsGroupAdmin(admin.ModelAdmin):
#     list_display = (
#         'pk',
#         'title',
#         'product_type',
#         'max_value'
#     )
#     list_display_links = ('title',)
#     search_fields = ('title',)
#     list_filter = ('product_type', 'options')
#     empty_value_display = EMPTY_FILLING


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
