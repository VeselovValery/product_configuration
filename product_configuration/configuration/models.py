from django.db import models


class ProductType(models.Model):
    STATUS_TYPE_CHOICES = [
        ('active', 'Действующий'),
        ('closed', 'Закрытый')
    ]
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Slug группы продуктов'
    )
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Название группы продуктов',
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_TYPE_CHOICES,
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
        on_delete=models.SET_NULL,
        null=True,
        related_name='basic_prices',
        verbose_name='Группа продукта',
        help_text='Группа, к которой относится базовый продукт'
    )
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Название базового продукта',
    )
    partnumber = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Номер продукта',
        help_text='Указывается номер продукта (если он известен)'
    )
    price = models.IntegerField(
        verbose_name='Цена гросс в руб. без НДС',
        help_text='Укажите цену гросс в руб. без НДС продукта (если она известна)'
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
        on_delete=models.SET_NULL,
        null=True,
        related_name='options',
        verbose_name='Группа продукта',
        help_text='Группа, к которой относится опция'
    )
    title = models.TextField(
        max_length=200,
        unique=True,
        verbose_name='Название опции',
    )

