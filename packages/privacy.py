from rest_framework_api_key.crypto import KeyGenerator
from django.contrib.auth.models import Group
from api.models import CustomAPIKey

def is_master_key(request):
    api_key = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
    hashed_api_key = KeyGenerator().hash(api_key)
    response = CustomAPIKey.objects.filter(hashed_key=hashed_api_key, name="FIZIT_MASTER_KEY").exists()
    return response

from rest_framework_api_key.crypto import KeyGenerator
from django.contrib.auth.models import Group
from api.models import CustomAPIKey

def is_master_key(request):
    api_key = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
    hashed_api_key = KeyGenerator().hash(api_key)
    return CustomAPIKey.objects.filter(hashed_key=hashed_api_key, name="FIZIT_MASTER_KEY").exists()

def is_user_authorized(request, parties):
    if is_master_key(request):
        return True
    
    api_key = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
    user = request.user if request.user.is_authenticated else None
    hashed_api_key = KeyGenerator().hash(api_key)

    party_codes = [party["party_code"] for party in parties]

    if api_key and CustomAPIKey.objects.filter(hashed_key=hashed_api_key).exists():
        # API authorization
        custom_api_key = CustomAPIKey.objects.get(hashed_key=hashed_api_key)
        api_parties = custom_api_key.parties.split(',')
        for party_code in party_codes:
            if party_code in api_parties:
                return True
    elif user and user.is_authenticated:
        # User authorization
        if user.is_staff:
            return True

        for group in user.groups.all():
            if group.name in party_codes:
                return True
    
    return False