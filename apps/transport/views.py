from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.matching.services import MatchingService

from .forms import TransportRequestForm
from .models import TransportRequest


@login_required
def request_create(request):
    if request.method == "POST":
        form = TransportRequestForm(request.POST)
        if form.is_valid():
            transport_request = form.save(commit=False)
            transport_request.owner = request.user
            transport_request.save()
            found = MatchingService().find_matches_for_request(transport_request)
            if found:
                messages.success(
                    request,
                    f"Opgaven er oprettet. {len(found)} chauffører kører næsten samme vej.",
                )
            else:
                messages.success(
                    request,
                    "Opgaven er oprettet. Du får besked, når en tur passer til ruten.",
                )
            return redirect(transport_request)
    else:
        form = TransportRequestForm()
    return render(request, "transport/request_form.html", {"form": form, "is_new": True})


@login_required
def request_detail(request, pk):
    transport_request = get_object_or_404(TransportRequest, pk=pk, owner=request.user)
    matches = transport_request.matches.select_related(
        "trip", "trip__driver"
    ).order_by("-match_score")
    return render(
        request,
        "transport/request_detail.html",
        {"transport_request": transport_request, "matches": matches},
    )


@login_required
def request_edit(request, pk):
    transport_request = get_object_or_404(TransportRequest, pk=pk, owner=request.user)
    if request.method == "POST":
        form = TransportRequestForm(request.POST, instance=transport_request)
        if form.is_valid():
            form.save()
            MatchingService().find_matches_for_request(transport_request)
            messages.success(request, "Opgaven er opdateret.")
            return redirect(transport_request)
    else:
        form = TransportRequestForm(instance=transport_request)
    return render(request, "transport/request_form.html", {"form": form, "is_new": False})


@login_required
def request_cancel(request, pk):
    transport_request = get_object_or_404(TransportRequest, pk=pk, owner=request.user)
    if request.method == "POST":
        transport_request.status = TransportRequest.Status.CANCELLED
        transport_request.save(update_fields=["status"])
        messages.info(request, "Opgaven er annulleret.")
        return redirect("dashboard")
    return render(
        request,
        "transport/request_confirm_cancel.html",
        {"transport_request": transport_request},
    )
