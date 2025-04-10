from mozilla_django_oidc.auth import OIDCAuthenticationBackend

class GoogleOIDCBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        email = claims.get('email')
        if email and email.endswith('@fizit.biz'):
            return self.UserModel.objects.filter(email__iexact=email)
        return self.UserModel.objects.none()

    def create_user(self, claims):
        user = super().create_user(claims)
        user.email = claims.get('email')
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()
        return user