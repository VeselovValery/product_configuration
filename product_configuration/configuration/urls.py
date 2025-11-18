from django.urls import path

from . import views

app_name = 'configuration'

urlpatterns = [
    path('', views.index, name='index'),
    path('autocomplete/', views.autocomplete_base_products, name='autocomplete'),
    path('create_basic', views.create_basic, name='basic'),
    path('get_options', views.get_options, name='options'),
    path('my_calculations/<slug:username>/', views.my_calculations, name='my_calculations'),
    path('find_calculations/', views.find_calculations, name='find_calculations')
]
