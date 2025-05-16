import base64
import os
from docusign_esign import ApiClient, EnvelopesApi, EnvelopeDefinition, Document, Signer, SignHere, Recipients, RecipientViewRequest

def create_envelope_and_recipient_view(token, base_path, account_id, signer_name, signer_email, party_code, return_url, contract_pdf_path):
    with open(contract_pdf_path, "rb") as file:
        document_base64 = base64.b64encode(file.read()).decode("utf-8")

    # Step 1: Define the envelope
    document = Document(
        document_base64=document_base64,
        name="Contract Document",
        file_extension="pdf",
        document_id="1"
    )

    signer = Signer(
        email=signer_email,
        name=signer_name,
        recipient_id="1",
        routing_order="1",
        client_user_id=party_code  # Required for embedded signing
    )

    sign_here = SignHere(
        anchor_string="/sig_here/",
        anchor_units="pixels",
        anchor_y_offset="10",
        anchor_x_offset="20"
    )
    signer.tabs = {"sign_here_tabs": [sign_here]}

    recipients = Recipients(signers=[signer])
    envelope = EnvelopeDefinition(
        email_subject="Please sign this contract",
        documents=[document],
        recipients=recipients,
        status="sent"
    )

    # Step 2: Create envelope
    api_client = ApiClient()
    api_client.host = base_path
    api_client.set_default_header("Authorization", f"Bearer {token}")
    envelopes_api = EnvelopesApi(api_client)

    results = envelopes_api.create_envelope(account_id, envelope_definition=envelope)
    envelope_id = results.envelope_id

    # Step 3: Create recipient view
    view_request = RecipientViewRequest(
        authentication_method="none",
        client_user_id=party_code,
        recipient_id="1",
        return_url=return_url,
        user_name=signer_name,
        email=signer_email
    )

    view_result = envelopes_api.create_recipient_view(account_id, envelope_id, recipient_view_request=view_request)
    return view_result.url