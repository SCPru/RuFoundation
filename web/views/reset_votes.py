from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect, resolve_url
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, CHANGE
from django.views.generic import FormView
from django.contrib.admin import site
from django.contrib import messages
from django.forms import Form

from web.models.articles import Vote


User = get_user_model()


@method_decorator(staff_member_required, name='dispatch')
class ResetUserVotesView(FormView):
    form_class = Form
    template_name = 'admin/web/user/user_action.html'

    def get_initial(self):
        initial = super(ResetUserVotesView, self).get_initial()
        return initial
    
    def get_user(self) -> User | None:
        user_id = self.kwargs.get('id') or None
        if user_id:
            return User.objects.get(pk=user_id)
        return None

    def get_context_data(self, **kwargs):
        context = super(ResetUserVotesView, self).get_context_data(**kwargs)
        context['title'] = 'Сбросить голоса пользователя'
        context['after_text'] = ('Вы уверены что хотите сбросить все голоса этого пользователя? '
                                 'Это действие нельзя будет отменить.')
        context['after_text_style'] = 'color: red'
        context['is_danger'] = True
        context['submit_btn'] = 'Сбросить'
        context.update(site.each_context(self.request))
        return context

    def get_success_url(self):
        return resolve_url('admin:index')

    def form_valid(self, form):
        user = self.get_user()
        if not user:
            messages.error(self.request, "Пользователь не существует")
        else:
            Vote.objects.filter(user=user).delete()

        LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(User).pk,
            object_id=user.pk,
            object_repr=str(user),
            action_flag=CHANGE,
            change_message='Голоса сброшены',
        )

        messages.success(self.request, "Голоса успешно сброшены")
        return redirect(self.get_success_url())
