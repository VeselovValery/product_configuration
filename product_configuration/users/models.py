from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser должен иметь is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('admin', 'Администратор'),
        ('fired', 'Уволенный')
    ]
    username = None
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Электронная почта',
        help_text='Электронная почта пользователя'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя пользователя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия пользователя'
    )
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='user'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'password',
        'first_name',
        'last_name'
    ]
    # ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    # ACCOUNT_USERNAME_REQUIRED = False
    # ACCOUNT_EMAIL_REQUIRED = True

    objects = CustomUserManager()

    class Meta:
        ordering = ['email']
        verbose_name = 'База данных пользователей>'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_working(self):
        return self.role == 'user' or self.role == 'admin'
