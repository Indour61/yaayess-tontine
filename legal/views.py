"""

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def accept_terms_view(request):
    if request.method == "POST" and request.POST.get("accept_terms") == "on":
        user = request.user
        user.terms_version = getattr(settings, "TERMS_VERSION", "v1.0-2025-09-07")
        user.terms_accepted_at = timezone.now()
        user.save(update_fields=["terms_version", "terms_accepted_at"])
        return redirect("/")  # ou ton dashboard
    return render(request, "legal/accept_terms.html")
"""