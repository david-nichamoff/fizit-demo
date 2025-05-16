import logging
from django.contrib.auth import logout
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, resolve_url
from django.urls import reverse_lazy

from api.utilities.logging import log_info

logger = logging.getLogger(__name__)

class DashboardLogoutView(LogoutView):
    next_page = reverse_lazy('dashboard_login')

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            log_info(logger, f"📤 Logging out dashboard user: {user}")
        else:
            log_info(logger, "📤 Dashboard logout called with no authenticated user.")

        logout(request)
        request.session.flush()
        return redirect(resolve_url(self.next_page))