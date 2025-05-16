import datetime

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from api.models import ContractApproval
from django.contrib import messages

from frontend.views.decorators.group import group_matches_customer

@group_matches_customer
def approve_contract_view(request, customer, contract_type, contract_idx, contract_release):
    if request.method == "POST":
        approval, created = ContractApproval.objects.get_or_create(
            contract_type=contract_type,
            contract_idx=contract_idx,
            contract_release=contract_release,
            party_code=customer
        )
        approval.approved = True
        approval.approved_by = request.user
        approval.approved_dt = datetime.datetime.utcnow()
        approval.save()
        messages.success(request, f"{customer} approved contract {contract_idx}.")
    
    return redirect(f"/dashboard/{customer}/view-contract/?contract_type={contract_type}&contract_idx={contract_idx}")