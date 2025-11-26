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
        verbose_name = 'Группы продуктов'

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
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug базового продукта'
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
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug опции'
    )
    name = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Наименование опции',
    )
    description = models.TextField(
        max_length=1024,
        default='Описание опции',
        verbose_name='Описание опции',
    )
    part_name = models.CharField(
        max_length=64,
        verbose_name='Часть имени для формирования наименования конечного продукта'
    )
    price = models.IntegerField(
        verbose_name='Цена опции в руб. без НДС'
    )
    coefficients = ArrayField(
        models.CharField(max_length=200),
        default=list,
        verbose_name='Коэффициенты для умножения',
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Текущий статус опции'
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Опция продукта'
        verbose_name_plural = 'Опции продуктов'

    def __str__(self):
        return self.name


class OptionsGroup(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='slug',
        on_delete=models.CASCADE,
        related_name='group_options',
        verbose_name='Группа продукта'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug группировки опции'
    )
    name = ArrayField(
        models.CharField(max_length=200),
        default=list,
        verbose_name='Возможные варианты группируемых опций (через запятую)',
    )
    max_value = models.IntegerField(
        verbose_name='Максимальное кол-во группируемых опций'
    )
    value = ArrayField(
        models.CharField(max_length=20),
        default=list,
        verbose_name='Возможные объемы подключения группируемых опций (через запятую)',
    )

    class Meta:
        ordering = ['pk']
        verbose_name = 'Группировка опций продукта'

    def __str__(self):
        """
        Возвращаем человеко-читаемое строковое представление.
        Поле `name` является ArrayField, поэтому по умолчанию это список.
        Для отображения в админке берём первое значение (если есть),
        иначе объединяем все элементы через запятую, а при пустом списке
        возвращаем понятный маркер с ID объекта.
        """
        if isinstance(self.name, list):
            if not self.name:
                return f'Группа опций #{self.pk}'
            # Показываем первый элемент как основное имя
            return self.name[0]
        # На случай, если в будущем тип поля изменится
        return str(self.name)


class Configuration(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        to_field='name',
        on_delete=models.CASCADE,
        related_name='product_configurations',
        verbose_name='Группа продукта'
    )
    basic_product = models.ForeignKey(
        BasicPrice,
        to_field='name',
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
