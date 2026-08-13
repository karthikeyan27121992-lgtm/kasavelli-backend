from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class SilentJWTAuthentication(JWTAuthentication):
    """
    JWTAuthentication that silently returns None (anonymous user) when the
    token is invalid or expired, instead of raising AuthenticationFailed.

    This allows public endpoints (permission_classes = [AllowAny]) to work
    even when the browser sends a stale/expired Authorization header.
    Authenticated endpoints still enforce authentication via their own
    permission classes (IsAuthenticated).
    """

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError):
            return None
