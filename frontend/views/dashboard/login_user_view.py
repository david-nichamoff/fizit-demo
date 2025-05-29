import logging
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.http import url_has_allowed_host_and_scheme

from api.utilities.logging import log_debug, log_info, log_warning, log_error

logger = logging.getLogger(__name__)

@method_decorator(csrf_protect, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class DashboardLoginView(LoginView):
    template_name = 'dashboard/login.html'
    redirect_authenticated_user = False

    def get(self, request, *args, **kwargs):
        log_warning(logger, f"📥 GET login page: next={request.GET.get('next')}")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        log_info(logger, f"✅ Form valid, user authenticated: {user}")
        redirect_to = self.get_redirect_url()
        log_info(logger, f"🔁 Redirecting to: {redirect_to}")
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        log_info(logger, f"➡️ Calculating success URL, next param: {next_url}")

        if next_url and next_url != self.request.path and url_has_allowed_host_and_scheme(next_url, self.request.get_host()):
            return next_url

        log_warning(logger, f"⚠️ Ignoring suspicious or recursive next URL: {next_url}")
        return reverse_lazy('list_contracts', kwargs={'customer': 'fizit'})