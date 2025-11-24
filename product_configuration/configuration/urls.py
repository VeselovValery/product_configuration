from django.urls import path

from . import views

app_name = 'configuration'

urlpatterns = [
    path('', views.index, name='index'),
    path('autocomplete', views.autocomplete_base_products, name='autocomplete'),
    path('get_options', views.get_options, name='get_options'),
    path('my_calculations/<slug:username>/', views.my_calculations, name='my_calculations')
]
