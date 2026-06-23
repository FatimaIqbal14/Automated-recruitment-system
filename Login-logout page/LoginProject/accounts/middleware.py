from django.shortcuts import redirect
from django.contrib import messages

class DeveloperAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We target any path starting with /admin/
        if request.path.startswith('/admin/'):
            # Allow logout requests to pass through so users can sign out cleanly
            if request.path.startswith('/admin/logout/'):
                return self.get_response(request)

            if request.user.is_authenticated:
                is_developer = False
                try:
                    is_developer = request.user.profile.is_developer
                except Exception:
                    pass

                if not (is_developer or request.user.is_superuser):
                    messages.error(request, "Access denied. Only Developers or Superusers can access the Django Admin.")
                    return redirect('dashboard')

        return self.get_response(request)
