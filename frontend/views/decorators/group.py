from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def group_matches_customer(view_func):
    @login_required
    def _wrapped_view(request, customer, *args, **kwargs):
        # Staff can access all dashboards
        if request.user.is_staff:
            return view_func(request, customer, *args, **kwargs)
        
        # Check if user's group matches customer
        if request.user.groups.filter(name__iexact=customer).exists():
            return view_func(request, customer, *args, **kwargs)
        
        # Otherwise, deny access
        raise PermissionDenied("You do not have access to this customer dashboard.")
    
    return _wrapped_view