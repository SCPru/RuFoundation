from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse
from django.views.generic import DetailView, UpdateView
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.template.loader import render_to_string
from django.views import View

from renderer import single_pass_render
from renderer.parser import RenderContext
from web.controllers import forum_reactions
from web.controllers.logging import add_action_log
from web.forms import ModeratorUserPublicInfoForm, ModeratorUserRolesForm, ModeratorUserStatusForm, UserProfileForm
from web.models.logs import ActionLogEntry
from web.models.users import User


MODERATION_STATE_OPTIONS = [
    {
        'value': ModeratorUserStatusForm.STATE_ACTIVE,
        'label': 'Активно',
        'help': 'Без пользовательского ограничения.',
    },
    {
        'value': ModeratorUserStatusForm.STATE_TEMPORARY,
        'label': 'Временно',
        'help': 'Вернется автоматически в указанное время.',
    },
    {
        'value': ModeratorUserStatusForm.STATE_DISABLED,
        'label': 'Бессрочно',
        'help': 'До ручного включения модератором.',
    },
]

STATUS_FIELDS = [
    'is_active',
    'inactive_until',
    'is_forum_active',
    'forum_inactive_until',
    'is_forum_reactions_disabled',
    'forum_reactions_disabled_until',
]


def profile_url(user: User):
    return reverse('users', kwargs={'pk': user.pk, 'slug': user.username})


def can_manage_profile_user(manager: User, target: User):
    if not manager.is_authenticated or not manager.has_perm('roles.manage_users'):
        return False
    if manager.is_superuser:
        return True
    if manager.pk == target.pk:
        return False
    return target.operation_index > manager.operation_index


def can_manage_profile_roles(manager: User, target: User):
    return can_manage_profile_user(manager, target) and manager.has_perm('roles.manage_roles')


def clear_user_role_caches(user: User):
    for key in ['operation_index', 'vote_role', 'name_tails', 'showcase', '_roles_cache', '_roles_perms_cache']:
        user.__dict__.pop(key, None)


def build_profile_context(request, target: User, **forms):
    if target.type == User.UserType.Wikidot:
        avatar = settings.WIKIDOT_AVATAR
        displayname = 'wd:' + target.wikidot_username
    else:
        avatar = target.get_avatar(default=settings.DEFAULT_AVATAR)
        displayname = target.username

    showcase = target.showcase
    can_manage_target = can_manage_profile_user(request.user, target)
    can_manage_roles = can_manage_profile_roles(request.user, target)

    ctx = {
        'object': target,
        'avatar': avatar,
        'displayname': displayname,
        'subtitle': ', '.join(showcase['titles']),
        'showcase_badges': showcase['badges'],
        'bio_rendered': single_pass_render(
            target.bio,
            RenderContext(article=None, source_article=None, path_params=None, user=request.user),
            'inline',
        ),
        'profile_url': profile_url(target),
        'can_manage_users': request.user.is_authenticated and request.user.has_perm('roles.manage_users'),
        'can_manage_target': can_manage_target,
        'can_manage_roles': can_manage_roles,
        'moderation_state_options': MODERATION_STATE_OPTIONS,
        'status_items': get_status_items(target),
    }

    if can_manage_target:
        ctx['manage_url'] = '%s?_popup=1' % reverse(
            'admin:%s_%s_change' % (target._meta.app_label, target._meta.model_name),
            args=[target.pk],
        )
        ctx['public_info_form'] = forms.get('public_info_form') or ModeratorUserPublicInfoForm(instance=target)
        ctx['status_form'] = forms.get('status_form') or ModeratorUserStatusForm(target_user=target)
        if can_manage_roles:
            ctx['roles_form'] = forms.get('roles_form') or ModeratorUserRolesForm(target_user=target)
    return ctx


def get_status_items(user: User):
    items = []
    if user.is_active:
        items.append({'kind': 'ok', 'label': 'Аккаунт активен'})
    elif user.inactive_until:
        items.append({'kind': 'danger', 'label': 'Аккаунт заблокирован временно', 'until': user.inactive_until})
    else:
        items.append({'kind': 'danger', 'label': 'Аккаунт заблокирован бессрочно'})

    if user.is_forum_active:
        items.append({'kind': 'ok', 'label': 'Форум активен'})
    elif user.forum_inactive_until:
        items.append({'kind': 'warning', 'label': 'Форум отключен временно', 'until': user.forum_inactive_until})
    else:
        items.append({'kind': 'warning', 'label': 'Форум отключен бессрочно'})

    if user.forum_reactions_disabled_until:
        items.append({'kind': 'warning', 'label': 'Реакции отключены', 'until': user.forum_reactions_disabled_until})
    elif user.is_forum_reactions_disabled:
        items.append({'kind': 'warning', 'label': 'Реакции отключены бессрочно'})
    elif forum_reactions.user_can_react(user):
        items.append({'kind': 'ok', 'label': 'Реакции включены'})
    return items


def render_profile_preview(request, target: User):
    return render_to_string('profile/_preview.html', build_profile_context(request, target), request=request)


def status_snapshot(user: User):
    return {field: getattr(user, field) for field in STATUS_FIELDS}


def changed_fields(before, target: User, fields):
    changes = {}
    for field in fields:
        after = getattr(target, field)
        if before.get(field) != after:
            changes[field] = {'from': str(before.get(field)), 'to': str(after)}
    return changes


def log_profile_change(manager: User, target: User, action: str, changes: dict):
    add_action_log(manager, ActionLogEntry.ActionType.ChangeProfileInfo, {
        'action': action,
        'target_user': {
            'id': target.id,
            'username': target.username,
        },
        'changes': changes,
    })


def wants_json(request):
    return 'application/json' in request.headers.get('Accept', '') or request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def redirect_url(request, target: User):
    next_url = request.POST.get('next') or request.GET.get('next') or profile_url(target)
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return next_url
    return profile_url(target)


class ProfileView(DetailView):
    model = User
    slug_field = "username"

    def get_queryset(self):
        return super().get_queryset().prefetch_related('roles', 'roles__category')

    def get_context_data(self, **kwargs):
        return build_profile_context(self.request, self.object)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        q = super().get_object(queryset=queryset)
        return q


class ProfilePreviewView(View):
    def get(self, request, pk, slug):
        target = get_object_or_404(User.objects.prefetch_related('roles', 'roles__category'), pk=pk)
        return HttpResponse(render_profile_preview(request, target))


class ModerateUserView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk, slug):
        target = get_object_or_404(User.objects.prefetch_related('roles', 'roles__category'), pk=pk)
        if not can_manage_profile_user(request.user, target):
            raise PermissionDenied

        action = request.POST.get('action')
        if action == 'save_public_info':
            return self.save_public_info(request, target)
        if action == 'save_status':
            return self.save_status(request, target)
        if action == 'save_roles':
            return self.save_roles(request, target)
        if action == 'toggle_account':
            return self.toggle_status(request, target, 'is_active', 'inactive_until', 'аккаунт')
        if action == 'toggle_forum':
            return self.toggle_status(request, target, 'is_forum_active', 'forum_inactive_until', 'форум')
        if action == 'toggle_reactions':
            return self.toggle_reactions(request, target)

        return self.finish(request, target, 'Неизвестное действие.', ok=False, status=400)

    def save_public_info(self, request, target: User):
        form = ModeratorUserPublicInfoForm(request.POST, request.FILES, instance=target)
        if not form.is_valid():
            return self.invalid_form(request, target, public_info_form=form)

        changed = form.changed_data
        form.save()
        if changed:
            log_profile_change(request.user, target, 'public_info', {'fields': changed})
        return self.finish(request, target, 'Публичная информация обновлена.')

    def save_status(self, request, target: User):
        form = ModeratorUserStatusForm(request.POST, target_user=target)
        if not form.is_valid():
            return self.invalid_form(request, target, status_form=form)

        before = status_snapshot(target)
        form.apply_to(target)
        changes = changed_fields(before, target, STATUS_FIELDS)
        target.save(update_fields=STATUS_FIELDS)
        if changes:
            log_profile_change(request.user, target, 'status', changes)
        return self.finish(request, target, 'Ограничения пользователя обновлены.')

    def save_roles(self, request, target: User):
        if not can_manage_profile_roles(request.user, target):
            raise PermissionDenied

        form = ModeratorUserRolesForm(request.POST, target_user=target)
        if not form.is_valid():
            return self.invalid_form(request, target, roles_form=form)

        old_roles = list(target.roles.order_by('slug').values_list('slug', flat=True))
        target.roles.set(form.cleaned_data['roles'])
        clear_user_role_caches(target)
        new_roles = list(target.roles.order_by('slug').values_list('slug', flat=True))
        if old_roles != new_roles:
            log_profile_change(request.user, target, 'roles', {'from': old_roles, 'to': new_roles})
        return self.finish(request, target, 'Роли пользователя обновлены.')

    def toggle_status(self, request, target: User, active_field: str, until_field: str, label: str):
        before = status_snapshot(target)
        new_value = not getattr(target, active_field)
        setattr(target, active_field, new_value)
        setattr(target, until_field, None)
        target.save(update_fields=[active_field, until_field])
        changes = changed_fields(before, target, [active_field, until_field])
        log_profile_change(request.user, target, f'toggle_{active_field}', changes)
        state = 'включен' if new_value else 'отключен'
        return self.finish(request, target, f'{label.capitalize()} {state}.')

    def toggle_reactions(self, request, target: User):
        before = status_snapshot(target)
        target.is_forum_reactions_disabled = not target.is_forum_reactions_disabled
        target.forum_reactions_disabled_until = None
        target.save(update_fields=['is_forum_reactions_disabled', 'forum_reactions_disabled_until'])
        changes = changed_fields(before, target, ['is_forum_reactions_disabled', 'forum_reactions_disabled_until'])
        log_profile_change(request.user, target, 'toggle_is_forum_reactions_disabled', changes)
        message = 'Реакции отключены.' if target.is_forum_reactions_disabled else 'Отключение реакций снято.'
        return self.finish(request, target, message)

    def invalid_form(self, request, target: User, **forms):
        if wants_json(request):
            form = next(iter(forms.values()))
            return JsonResponse({'ok': False, 'errors': form.errors.get_json_data()}, status=400)
        context = build_profile_context(request, target, **forms)
        return render(request, 'profile/user.html', context, status=400)

    def finish(self, request, target: User, message: str, ok=True, status=200):
        if wants_json(request):
            target.refresh_from_db()
            clear_user_role_caches(target)
            return JsonResponse({
                'ok': ok,
                'message': message,
                'preview': render_profile_preview(request, target),
            }, status=status)
        if ok:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect(redirect_url(request, target))


class ChangeProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    redirect_field_name = 'to'

    def get_success_url(self):
        return "/-/profile/edit"

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.fields['bio'].label += ' (поддерживается разметка)'
        return form
