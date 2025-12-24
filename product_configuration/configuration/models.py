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
    series = models.TextField(
        max_length=200,
        null=True,
        default=None,
        verbose_name='Серия группы продуктов',
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
    part_number = models.TextField(
        max_length=200,
        default='по запросу',
        verbose_name='Артикул опционального продукта'
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
    fs_current_jockey = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Диапазон тока жокей насоса в FS'
    )
    mpc_neutral = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Наличие нейтрали в MPC'
    )
    mecable = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Вариант опции удлинения кабеля для МЕ'
    )
    meavr = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Вариант опции АВР для МЕ'
    )
    fscable = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Вариант опции удлинения кабеля для FS'
    )
    mpcavr = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Вариант опции АВР для МPC'
    )
    mpcammeter = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Вариант опции Амперметр для МPC'
    )
    mpccable = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Вариант опции удлинения кабеля для MPC'
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Базовый продукт'
        verbose_name_plural = 'Базовые продукты'

    def __str__(self):
        return self.name


class OptionsProfile(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='options_profile',
        verbose_name='Группа продукта'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug опции'
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
    values = ArrayField(
        models.CharField(max_length=30),
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
        return f'{self.name} ({self.product_type.series})'


class OptionsPrice(models.Model):
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Название варианта опции',
    )
    option = models.ForeignKey(
        OptionsProfile,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='options_price',
        verbose_name='Опция'
    )
    variant = models.IntegerField(
        verbose_name='Номер варианта опции'
    )
    price = models.IntegerField(
        verbose_name='Цена опции в руб. без НДС'
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Стоимость опции'
        verbose_name_plural = 'Стоимость опций'

    def __str__(self):
        return self.title


class OptionsConstraint(models.Model):
    title = models.CharField(
        max_length=200
    )
    product_type = models.ManyToManyField(
        ProductType,
        related_name='options_constraints',
        verbose_name='Группа продукта'
    )
    options = models.ManyToManyField(
        OptionsProfile,
        related_name='constraints',
        verbose_name='Опции входящие в группу'
    )
    max_total_value = models.IntegerField(
        verbose_name='Максимальное кол-во однотипных опций'
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Ограничение по суммарному объему опций'
        verbose_name_plural = 'Ограничения по суммарному объему опций'

    def __str__(self):
        return self.title


class OptionPartNumber(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='product_option_partnumber',
        verbose_name='Группа продукта'
    )
    name = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Наименование опционального продукта'
    )
    part_number = models.TextField(
        max_length=200,
        verbose_name='Артикул опционального продукта'
    )
    options_value = ArrayField(
        models.TextField(max_length=256),
        default=list,
        verbose_name='Объем подключения опций (список)'
    )
    cost_without_vat = models.IntegerField(
        null=True,
        verbose_name='Стоимость опционального продукта без НДС'
    )
    cost_with_vat = models.IntegerField(
        null=True,
        verbose_name='Стоимость опционального продукта c НДС'
    )

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'part_number')
        verbose_name = 'Стоимость опционального оборудования'
        verbose_name_plural = 'Стоимость опционального оборудования'

    def __str__(self):
        return self.name


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
        OptionsProfile,
        related_name='configurations',
        verbose_name='Опции конечного продукта'
    )
    options_value = ArrayField(
        models.TextField(max_length=256),
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
