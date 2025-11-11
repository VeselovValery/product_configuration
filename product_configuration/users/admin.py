from django.contrib import admin
from django.contrib.auth import get_user_model

EMPTY_FILLING = '-пусто-'
User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'email',
        'password',
        'first_name',
        'last_name',
        'role'
    )
    list_display_links = ('email',)
    search_fields = ('email',)
    list_filter = ('email',)
    empty_value_display = EMPTY_FILLING
