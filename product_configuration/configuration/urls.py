from django.urls import path

from . import views

app_name = 'configuration'

urlpatterns = [
    path('', views.index, name='index'),
    path('my_calculations/<slug:username>/', views.my_calculations, name='my_calculations'),
    path('find_calculations/', views.find_calculations, name='find_calculations')
]
