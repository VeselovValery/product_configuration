from django.shortcuts import render


def index(request):
    return render(request, 'configuration/index.html')


def my_calculations(request):
    return render(request, 'configuration/my_calculation.html')


def find_calculations(request):
    return render(request, 'configuration/find.html')
