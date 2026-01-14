from django.urls import path

from . import views

app_name = 'configuration'

urlpatterns = [
    path('', views.index, name='index'),
    path('autocomplete', views.autocomplete_base_products, name='autocomplete'),
    path('get_options', views.get_options, name='get_options'),
    path('validate_options', views.validate_options, name='validate_options'),
    # path('my_calculations/<int:pk>/', views.MyCalculations.as_view(), name='my_calculations'),
    path('upload_data/', views.upload_data, name='upload_data'),
    path('export_data/', views.export_data, name='export_data'),
]
