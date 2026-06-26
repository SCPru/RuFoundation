from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone

from web.models.roles import Role
from web.models.users import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'username': forms.TextInput()
        }


class ModeratorUserPublicInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'wikidot_username', 'first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'off'}),
            'wikidot_username': forms.TextInput(attrs={'autocomplete': 'off'}),
            'bio': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        self.target_user = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if self.target_user and self.target_user.type != User.UserType.Wikidot:
            self.fields.pop('wikidot_username', None)
        if 'bio' in self.fields:
            self.fields['bio'].label += ' (поддерживается разметка)'


class ModeratorUserStatusForm(forms.Form):
    STATE_ACTIVE = 'active'
    STATE_TEMPORARY = 'temporary'
    STATE_DISABLED = 'disabled'

    STATE_CHOICES = (
        (STATE_ACTIVE, 'Активно'),
        (STATE_TEMPORARY, 'Временно отключено'),
        (STATE_DISABLED, 'Отключено бессрочно'),
    )

    account_state = forms.ChoiceField(label='Аккаунт', choices=STATE_CHOICES, widget=forms.RadioSelect)
    account_until = forms.DateTimeField(
        label='Бан до',
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
    )
    forum_state = forms.ChoiceField(label='Форум', choices=STATE_CHOICES, widget=forms.RadioSelect)
    forum_until = forms.DateTimeField(
        label='Форум отключен до',
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
    )
    reactions_state = forms.ChoiceField(label='Реакции', choices=STATE_CHOICES, widget=forms.RadioSelect)
    reactions_forced_disabled = forms.BooleanField(
        label='Принудительно отключить реакции форума',
        required=False,
    )
    reactions_disabled_until = forms.DateTimeField(
        label='Отключить реакции до',
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
    )

    state_meta = {
        STATE_ACTIVE: ('Активно', 'Пользователь может пользоваться возможностью без ограничений.'),
        STATE_TEMPORARY: ('Временно', 'Возможность вернется автоматически в указанное время.'),
        STATE_DISABLED: ('Бессрочно', 'Возможность отключена до ручного включения.'),
    }

    def __init__(self, *args, target_user: User=None, **kwargs):
        self.target_user = target_user
        super().__init__(*args, **kwargs)
        if target_user and not self.is_bound:
            self.initial.update({
                'account_state': self._state_from(target_user.is_active, target_user.inactive_until),
                'account_until': self._datetime_initial(target_user.inactive_until),
                'forum_state': self._state_from(target_user.is_forum_active, target_user.forum_inactive_until),
                'forum_until': self._datetime_initial(target_user.forum_inactive_until),
                'reactions_forced_disabled': target_user.is_forum_reactions_disabled,
                'reactions_disabled_until': self._datetime_initial(target_user.forum_reactions_disabled_until),
                'reactions_state': self._state_from(not target_user.is_forum_reactions_disabled, target_user.forum_reactions_disabled_until),
            })

    @classmethod
    def _state_from(cls, is_active, inactive_until):
        if inactive_until:
            return cls.STATE_TEMPORARY
        if is_active:
            return cls.STATE_ACTIVE
        return cls.STATE_DISABLED

    @staticmethod
    def _datetime_initial(value):
        if not value:
            return None
        return timezone.localtime(value).replace(second=0, microsecond=0)

    def clean(self):
        cleaned_data = super().clean()
        checks = (
            ('account_state', 'account_until', 'аккаунта'),
            ('forum_state', 'forum_until', 'форума'),
        )
        now = timezone.now()
        for state_field, until_field, label in checks:
            if cleaned_data.get(state_field) != self.STATE_TEMPORARY:
                continue
            until = cleaned_data.get(until_field)
            if not until:
                self.add_error(until_field, f'Укажите время окончания временного ограничения {label}.')
            elif until <= now:
                self.add_error(until_field, 'Время окончания должно быть в будущем.')
        # Validate reactions state if provided (new radio-style control)
        if 'reactions_state' in cleaned_data:
            if cleaned_data.get('reactions_state') == self.STATE_TEMPORARY:
                reactions_until = cleaned_data.get('reactions_disabled_until')
                if not reactions_until:
                    self.add_error('reactions_disabled_until', 'Укажите время окончания временного ограничения реакций.')
                elif reactions_until <= now:
                    self.add_error('reactions_disabled_until', 'Время окончания должно быть в будущем.')
        else:
            # backward-compat: if boolean was used ensure until (if present) is in the future
            reactions_until = cleaned_data.get('reactions_disabled_until')
            if cleaned_data.get('reactions_forced_disabled') and reactions_until and reactions_until <= now:
                self.add_error('reactions_disabled_until', 'Время окончания должно быть в будущем.')
        return cleaned_data

    def apply_to(self, user: User):
        self._apply_state(user, 'is_active', 'inactive_until', self.cleaned_data['account_state'], self.cleaned_data.get('account_until'))
        self._apply_state(user, 'is_forum_active', 'forum_inactive_until', self.cleaned_data['forum_state'], self.cleaned_data.get('forum_until'))
        # Support radio-style reactions_state if present, otherwise fall back to boolean
        if 'reactions_state' in self.cleaned_data:
            state = self.cleaned_data.get('reactions_state')
            if state == self.STATE_ACTIVE:
                user.is_forum_reactions_disabled = False
                user.forum_reactions_disabled_until = None
            elif state == self.STATE_TEMPORARY:
                user.is_forum_reactions_disabled = True
                user.forum_reactions_disabled_until = self.cleaned_data.get('reactions_disabled_until')
            else:
                user.is_forum_reactions_disabled = True
                user.forum_reactions_disabled_until = None
        else:
            reactions_disabled = self.cleaned_data.get('reactions_forced_disabled')
            user.is_forum_reactions_disabled = reactions_disabled
            user.forum_reactions_disabled_until = self.cleaned_data.get('reactions_disabled_until') if reactions_disabled else None

    @classmethod
    def _apply_state(cls, user, active_field, until_field, state, until):
        if state == cls.STATE_ACTIVE:
            setattr(user, active_field, True)
            setattr(user, until_field, None)
        elif state == cls.STATE_TEMPORARY:
            setattr(user, active_field, False)
            setattr(user, until_field, until)
        else:
            setattr(user, active_field, False)
            setattr(user, until_field, None)


class ModeratorUserRolesForm(forms.Form):
    roles = forms.ModelMultipleChoiceField(
        label='Роли',
        queryset=Role.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, target_user: User=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['roles'].queryset = Role.objects.exclude(slug__in=['everyone', 'registered'])
        if target_user and not self.is_bound:
            self.initial['roles'] = target_user.roles.exclude(slug__in=['everyone', 'registered'])


class InviteForm(forms.Form):
    _selected_user = forms.IntegerField(widget=forms.MultipleHiddenInput, required=False)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'vTextField'}))
    roles = forms.ModelMultipleChoiceField(label='Роли', queryset=Role.objects.exclude(slug__in=['everyone', 'registered']), required=False)


class CreateAccountForm(forms.Form):
    username = forms.CharField(label='Имя пользователя', required=True, validators=[RegexValidator(r'^[A-Za-z0-9_-]+$', 'Некорректное имя пользователя')])
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput(), required=True)

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают')
        return cd['password2']


class CreateBotForm(forms.Form):
    username = forms.CharField(
        label='Ник бота',
        required=True,
        validators=[
                RegexValidator(r'^[A-Za-z0-9_-]+$', 'Некорректное имя пользователя')
            ]
        )
