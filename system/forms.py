from django import forms


class InviteForm(forms.Form):
    _selected_user = forms.IntegerField(widget=forms.MultipleHiddenInput, required=False)
    email = forms.EmailField()


class CreateAccountForm(forms.Form):
    username = forms.CharField(label="Имя пользователя", required=True)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(), required=True)
