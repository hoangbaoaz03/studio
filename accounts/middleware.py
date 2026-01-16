from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout

class ApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Exclude admin panel and public pages if necessary, but checking is_authenticated is key.
        # Check if user is authenticated
        if request.user.is_authenticated:
            # If user is not approved and not superuser (admin should always be allowed)
            if not request.user.is_approved and not request.user.is_superuser:
                # Avoid redirect loop if already at login or logout
                # Note: 'login' url might be different if using standard auth.
                # Usually it is /accounts/login/
                
                if request.path == reverse('logout') or request.path_info.startswith('/admin/'):
                     # Allow admin site access? No, is_approved applies to everyone except superuser.
                     pass 

                # Log them out and redirect
                messages.error(request, "Your account is pending approval by the administrator.")
                logout(request)
                return redirect('login')

        response = self.get_response(request)
        return response
