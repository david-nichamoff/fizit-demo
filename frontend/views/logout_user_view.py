import logging
from django.contrib.auth import logout
from django.shortcuts import redirect
from urllib.parse import urlencode

from api.utilities.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)
def oidc_logout(request):

    logger.info("📤 OIDC logout view called for user: %s", request.user)
    logout(request)
    logger.info("✅ Django session logged out, redirecting to Google logout")
    return redirect('/')