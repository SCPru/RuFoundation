from django import forms


class InviteForm(forms.Form):
    email = forms.EmailField()


class CreateAccountForm(forms.Form):
    username = forms.CharField(label="Имя пользователя", required=True)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(), required=True)
