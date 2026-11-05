from django.shortcuts import render

from .models import Disbursement
from .services import monthly, totals


def impact(request):
    return render(request, "donations/impact.html", {
        "impact": totals(),
        "months": monthly(),
        "disbursements": Disbursement.objects.select_related("cause")[:20],
    })
