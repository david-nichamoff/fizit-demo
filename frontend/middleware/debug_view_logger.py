import logging

from django.utils.deprecation import MiddlewareMixin
from api.utilities.logging import log_warning

logger = logging.getLogger(__name__)

class ViewLoggerMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        log_warning(logger, f"🔍 Matched view: {view_func.__module__}.{view_func.__name__} for path: {request.path}")
from django.utils.deprecation import MiddlewareMixin
from api.utilities.logging import log_warning

logger = logging.getLogger(__name__)

class ViewLoggerMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        log_warning(logger, f"🔍 Matched view: {view_func.__module__}.{view_func.__name__} for path: {request.path}")