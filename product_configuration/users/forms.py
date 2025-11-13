from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class CreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name')


class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'autofocus': True}),
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        model = get_user_model()
        if email and password:
            try:
                user = model.objects.get(email__iexact=email)
            except model.DoesNotExist:
                raise forms.ValidationError('Неверный email или пароль.')
            if not user.check_password(password):
                raise forms.ValidationError('Неверный email или пароль.')
            if not user.is_active:
                raise forms.ValidationError('Аккаунт неактивен.')
            self.user_cache = user
        return self.cleaned_data
