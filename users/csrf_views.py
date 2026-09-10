"""
Minimal CSRF-token endpoint for the React frontend.

The React dev server (localhost:5173) and the Django API (127.0.0.1:8000)
run on different origins, so the csrftoken cookie set by the login response
is not available to DRF's SessionAuthentication for cross-origin POSTs.

This view sets the csrftoken cookie via ensure_csrf_cookie and returns the
token in the JSON body so the frontend can send it as the X-CSRFToken header
on subsequent requests.

It EXISTS ONLY because the frontend is a separate origin in development.
It deliberately does NOT disable CSRF, does not use csrf_exempt, and does not
change the existing session-authentication model. CSRF is still fully
enforced on every unsafe request.
"""
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})