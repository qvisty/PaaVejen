from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log
from apps.transport.models import TransportRequest

from .models import Report


@login_required
def report_request(request, request_pk):
    """Rapportér en mistænkelig transportopgave, jf. PRD afsnit 19."""
    transport_request = get_object_or_404(TransportRequest, pk=request_pk)
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        if reason:
            report = Report.objects.create(
                reporter=request.user,
                transport_request=transport_request,
                reason=reason,
            )
            log("report_created", user=request.user, report_id=report.pk)
            messages.success(
                request, "Tak for din rapport. Vi kigger på den hurtigst muligt.",
            )
            return redirect("dashboard")
        messages.error(request, "Skriv en kort begrundelse.")
    return render(
        request,
        "moderation/report_form.html",
        {"transport_request": transport_request},
    )
