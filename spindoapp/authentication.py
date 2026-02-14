from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import AllLog


class CustomJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):

        user_id = validated_token.get('user_id')

        if not user_id:
            raise AuthenticationFailed('Token contained no user_id')

        try:
            user = AllLog.objects.get(id=user_id)
        except AllLog.DoesNotExist:
            raise AuthenticationFailed('User not found')

        return user
