from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.constants import STATUS_CHOICES


class ProductType(models.Model):
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug группы продуктов'
    )
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Наименование группы продуктов',
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Текущий статус группы продуктов'
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Группы продуктов'

    def __str__(self):
        return self.title


class BasicPrice(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='title',
        on_delete=models.CASCADE,
        related_name='basic_prices',
        verbose_name='Группа продукта'
    )
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Наименование базового продукта',
    )
    partnumber = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Номер продукта'
    )
    price = models.IntegerField(
        verbose_name='Цена базового продукта в руб. без НДС'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Текущий статус базового продукта'
    )

    class Meta:
        ordering = ['-pk']
        verbose_name = 'Базовый продукт'
        verbose_name_plural = 'Базовые продукты'

    def __str__(self):
        return self.title


class OptionsPrice(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='title',
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='Группа продукта'
    )
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Наименование опции',
    )
    part_name = models.CharField(
        max_length=64,
        verbose_name='Часть имени для формирования наименования конечного продукта'
    )
    price = models.IntegerField(
        verbose_name='Цена опции в руб. без НДС'
    )
    value = ArrayField(
        models.CharField(max_length=20),
        default=list,
        verbose_name='Возможные объемы подключения опций (через запятую)',
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Текущий статус опции'
    )


class Configuration(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='title',
        on_delete=models.CASCADE,
        related_name='product_configurations',
        verbose_name='Группа продукта'
    )
    basic_product = models.ForeignKey(
        BasicPrice,
        to_field='title',
        on_delete=models.CASCADE,
        related_name='configurations',
        verbose_name='Базовый продукт'
    )
    options = models.ManyToManyField(
        OptionsPrice,
        related_name='configurations',
        verbose_name='Опции конечного продукта'
    )
    options_value = ArrayField(
        models.CharField(max_length=256),
        default=list,
        verbose_name='Объем каждой опции (список)'
    )
    name = models.TextField(
        max_length=512,
        unique=True,
        verbose_name='Наименование конечного продукта',
    )
    cost = models.IntegerField(
        verbose_name='Стоимость конечного продукта в руб. без НДС'
    )
    author = models.ForeignKey(
        get_user_model(),
        to_field='email',
        on_delete=models.SET_NULL,
        null=True,
        related_name='author_configuration',
        verbose_name='Автор расчета'
    )
    date_create = models.DateTimeField(
        verbose_name='Дата создания расчета',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-date_create']
        verbose_name = 'Расчет'
        verbose_name_plural = 'Расчеты'

    def __str__(self):
        return self.name
