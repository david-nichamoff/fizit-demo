import requests
import urllib.parse

from django.shortcuts import redirect
from django.conf import settings
from django.http import HttpResponse

from api.utilities.pkce import generate_pkce_pair
from api.utilities.docusign import create_envelope_and_recipient_view


def start_docusign_auth(request):
    code_verifier, code_challenge = generate_pkce_pair()
    request.session['docusign_code_verifier'] = code_verifier

    base_url = "https://account.docusign.com/oauth/auth"
    query = {
        "response_type": "code",
        "scope": "signature",
        "client_id": settings.DOCUSIGN_INTEGRATION_KEY,
        "redirect_uri": settings.DOCUSIGN_REDIRECT_URI,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

    return redirect(f"{base_url}?{urllib.parse.urlencode(query)}")

def docusign_callback(request):
    code = request.GET.get("code")
    code_verifier = request.session.get("docusign_code_verifier")

    if not code or not code_verifier:
        return HttpResponse("Missing code or verifier", status=400)

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.DOCUSIGN_INTEGRATION_KEY,
        "redirect_uri": settings.DOCUSIGN_REDIRECT_URI,
        "code_verifier": code_verifier,
    }

    token_url = "https://account.docusign.com/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(token_url, data=data, headers=headers)
    if resp.status_code == 200:
        token_data = resp.json()
        access_token = token_data["access_token"]
        # Store this in session or hand off to create recipient view
        return HttpResponse(f"Access token: {access_token}")
    else:
        return HttpResponse(f"Token exchange failed: {resp.text}", status=400)

def launch_signing_session(request):
    token = request.session.get("docusign_token")
    signer_name = request.user.get_full_name()
    signer_email = request.user.email
    party_code = "FLOATCO"  # Or dynamically pull from session/contract
    return_url = f"{settings.BASE_URL}/dashboard/contract/signed/"
    contract_pdf_path = "path/to/your/static/contract.pdf"  # Replace with actual logic

    api_base = "https://demo.docusign.net/restapi"  # Change to production base if needed
    account_id = request.session.get("docusign_account_id")

    if not token or not account_id:
        return HttpResponse("Missing token or account ID", status=400)

    signing_url = create_envelope_and_recipient_view(
        token, api_base, account_id,
        signer_name, signer_email,
        party_code, return_url,
        contract_pdf_path
    )

    return redirect(signing_url)