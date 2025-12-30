from django.contrib import admin

from .models import (
    ProductType,
    BasicPrice,
    OptionsProfile,
    OptionsPrice,
    OptionsConstraint,
    Configuration,
    OptionPartNumber
)
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
        'price'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('product_type', 'status')
    empty_value_display = EMPTY_FILLING


@admin.register(OptionsProfile)
class OptionsProfileAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'slug',
        'name',
        'product_type'
    )
    list_display_links = ('name',)
    search_fields = ('slug', 'name',)
    list_filter = ('product_type', 'status')
    empty_value_display = EMPTY_FILLING


@admin.register(OptionsPrice)
class OptionsPriceAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'option',
        'variant',
        'price'
    )
    list_display_links = ('title',)
    search_fields = ('title',)
    list_filter = ('option',)
    empty_value_display = EMPTY_FILLING


@admin.register(OptionsConstraint)
class OptionsConstraintAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'max_total_value'
    )
    list_display_links = ('title',)
    search_fields = ('title',)
    list_filter = ('product_type', 'options')
    empty_value_display = EMPTY_FILLING


@admin.register(OptionPartNumber)
class OptionPartNumberAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'part_number'
    )
    list_display_links = ('name',)
    search_fields = ('name', 'part_number')
    empty_value_display = EMPTY_FILLING


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'product_type',
        'cost_without_vat',
        'cost_with_vat'
    )
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('product_type', 'basic_product', 'author', 'options')
    empty_value_display = EMPTY_FILLING
