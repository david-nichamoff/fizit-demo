import logging
from django.contrib.auth import logout
from django.shortcuts import redirect

from api.utilities.logging import log_info

logger = logging.getLogger(__name__)

def oidc_logout_view(request):
    logger.info("📤 OIDC logout view called for user: %s", request.user)

    # End the Django session
    logout(request)
    logger.info("✅ Django session logged out")

    # Redirect to Google's logout cascade, then back to this host's root
    final_redirect = request.build_absolute_uri("/")
    google_logout_url = (
        "https://accounts.google.com/Logout"
        "?continue=https://appengine.google.com/_ah/logout"
        f"?continue={final_redirect}"
    )

    logger.info("🔁 Redirecting to Google logout chain -> %s", google_logout_url)
    return redirect(google_logout_url)