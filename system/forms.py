from django import forms
from django.core.validators import RegexValidator

from system.models import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', "bio", "avatar"]
        widgets = {
            'username': forms.TextInput()
        }


class InviteForm(forms.Form):
    _selected_user = forms.IntegerField(widget=forms.MultipleHiddenInput, required=False)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'vTextField'}))
    is_editor = forms.BooleanField(label='Статус участника', required=False)


class CreateAccountForm(forms.Form):
    username = forms.CharField(label="Имя пользователя", required=True, validators=[RegexValidator(r'^[A-Za-z0-9_-]+$', 'Некорректное имя пользователя')])
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput(), required=True)

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают')
        return cd['password2']


class CreateBotForm(forms.Form):
    username = forms.CharField(label="Ник бота", required=True, validators=[
        RegexValidator(r'^[A-Za-z0-9_-]+$', 'Некорректное имя пользователя')])

