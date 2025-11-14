from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm, CustomLoginForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('configuration:index')
    template_name = 'users/signup.html'


class CustomLogin(LoginView):
    form_class = CustomLoginForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            email = form.cleaned_data['username']
            user = get_object_or_404(get_user_model(), email=email)
            if user.is_working and user.is_active:
                return self.form_valid(form)
            else:
                return render(request, 'users/login_user_not_working.html')
        else:
            return self.form_invalid(form)
