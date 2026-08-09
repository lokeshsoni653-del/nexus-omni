from omnimind.backend.api.auth import get_authenticated_user

# Alias for backwards compatibility with earlier routes
get_current_user = get_authenticated_user

__all__ = ["get_current_user", "get_authenticated_user"]
