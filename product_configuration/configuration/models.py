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
    name = models.TextField(
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
        verbose_name = 'Группа продукта'
        verbose_name_plural = 'Группы продуктов'

    def __str__(self):
        return self.name


class BasicPrice(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='basic_prices',
        verbose_name='Группа продукта'
    )
    name = models.TextField(
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
        ordering = ['pk']
        verbose_name = 'Базовый продукт'
        verbose_name_plural = 'Базовые продукты'

    def __str__(self):
        return self.name


class OptionsPrice(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='Группа продукта'
    )
    name = models.TextField(
        max_length=200,
        verbose_name='Наименование опции',
    )
    description = models.TextField(
        max_length=1024,
        default='Описание опции',
        verbose_name='Описание опции',
    )
    part_name = models.CharField(
        max_length=64,
        verbose_name='Код опции'
    )
    price = models.IntegerField(
        verbose_name='Цена опции в руб. без НДС'
    )
    values = ArrayField(
        models.IntegerField(),
        default=list,
        verbose_name='Объемы подключения опции',
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Текущий статус опции'
    )

    class Meta:
        ordering = ['pk']
        unique_together = ('product_type', 'name')
        verbose_name = 'Опция продукта'
        verbose_name_plural = 'Опции продуктов'

    def __str__(self):
        return self.name


class OptionsCoef(models.Model):
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Названия коэффициента опции',
    )
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='options_coef',
        verbose_name='Группа продукта'
    )
    option = models.ForeignKey(
        OptionsPrice,
        on_delete=models.CASCADE,
        related_name='options_coef',
        verbose_name='Группа продукта'
    )
    name_coef = models.CharField(
        max_length=200,
        verbose_name='Наименование коэффициента',
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Коэффициент опции'
        verbose_name_plural = 'Коэффициенты опций'

    def __str__(self):
        return self.title


class OptionsGroup(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='group_options',
        verbose_name='Группа продукта'
    )
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Названия группы опций',
    )
    # options = ArrayField(
    #     models.CharField(max_length=200),
    #     default=list,
    #     verbose_name='Возможные варианты группируемых опций (через запятую)',
    # )
    options = models.ManyToManyField(
        OptionsPrice,
        related_name='options_group',
        verbose_name='Опции входящие в группу'
    )
    max_value = models.IntegerField(
        verbose_name='Максимальное кол-во группируемых опций'
    )
    value = ArrayField(
        models.IntegerField(),
        default=list,
        verbose_name='Объемы подключения опций, входящих в группу',
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Группа опций продукта'
        verbose_name_plural = 'Группы опций продуктай'

    def __str__(self):
        return self.title


class Configuration(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='product_configurations',
        verbose_name='Группа продукта'
    )
    basic_product = models.ForeignKey(
        BasicPrice,
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
        verbose_name='Объем подключения опций (список)'
    )
    name = models.TextField(
        max_length=512,
        verbose_name='Наименование конечного продукта',
    )
    cost = models.IntegerField(
        verbose_name='Стоимость конечного продукта '
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
