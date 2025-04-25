import os
from datetime import datetime
from pathlib import Path
from weasyprint import HTML
from dateutil.parser import isoparse
from django.conf import settings
from django.template.loader import render_to_string

def generate_contract_report(contract, parties, transactions, artifacts, settlements, contract_idx, contract_type, logo_relative_path, template_name):
    # Prepare fields
    if contract.get("service_fee_pct") is not None:
        contract["service_fee_pct"] = round(float(contract["service_fee_pct"]) * 100, 4)

    for transaction in transactions:
        transaction["transact_dt"] = isoparse(transaction["transact_dt"])
        if transaction.get("advance_pay_dt"):
            transaction["advance_pay_dt"] = isoparse(transaction["advance_pay_dt"])

    for artifact in artifacts:
        artifact["added_dt"] = isoparse(artifact["added_dt"])

    # Resolve logo path
    logo_file_path = os.path.join(settings.BASE_DIR, logo_relative_path)
    logo_url = f'file://{logo_file_path}'

    # Render HTML
    html_string = render_to_string(template_name, {
        "contract": contract,
        "parties": parties,
        "transactions": transactions,
        "artifacts": artifacts,
        "settlements": settlements,
        "contract_idx": contract_idx,
        "contract_type": contract_type,
        "report_date": datetime.utcnow(),
        "logo_url": logo_url
    })

    # Generate PDF
    pdf = HTML(string=html_string, base_url=str(Path(settings.BASE_DIR) / "frontend/templates/reports/")).write_pdf()

    return pdf