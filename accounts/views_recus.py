from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Payment


@login_required
def mes_recus(request):

    member = getattr(request.user, "member", None)

    payments = []

    if member:
        payments = Payment.objects.filter(member=member).order_by("-created_at")

    return render(request, "accounts/mes_recus.html", {
        "payments": payments
    })