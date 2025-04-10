from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def get_user(request):
    user = request.user
    return JsonResponse({
        'username': user.username,
        'first_name': user.first_name,
        'is_authenticated': user.is_authenticated,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })