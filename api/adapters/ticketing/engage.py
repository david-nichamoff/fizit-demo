import requests
from datetime import timedelta
import logging

import api.managers.secrets_manager as secrets_manager
import api.managers.config_manager as config_manager

class EngageAPI:
    def __init__(self):
        self.keys = secrets_manager.load_keys()
        self.config = config_manager.load_config()
        self.logger = logging.getLogger(__name__)

    def get_tickets(self, contract, engage_src, engage_dest, start_date, end_date):
        """Fetch tickets from the Engage API."""
        tickets = []
        url = f'{self.config["engage_uri"]}/v2/tickets'
        headers = {
            'x-api-key': engage_src.api_key,
            'businessID': str(engage_src.src_id),
            'Content-Type': 'application/json'
        }
        params = {
            "approvedate_before": end_date.strftime('%Y-%m-%d'),
            "approvedate_after": start_date.strftime('%Y-%m-%d')
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            engage_tickets = response.json().get("data", [])

            for engage_ticket in engage_tickets:
                ticket_detail_url = f'{self.config["engage_uri"]}/v2/tickets/{engage_ticket["ID"]}/tali'
                engage_detail = requests.get(ticket_detail_url, headers=headers).json().get("data", {})
                ticket = {
                    "contract_idx": contract["contract_idx"],
                    "contract_name": contract["contract_name"],
                    "ticket_id": engage_detail.get("ticketID"),
                    "approved_dt": engage_detail.get("approveDate"),
                    "ticket_amt": round(engage_detail.get("totalAmount", 0), 2),
                    "ticket_data": engage_detail,
                }
                tickets.append(ticket)

            return tickets
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching tickets: {e}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from e

    def get_invoices(self, contract, engage_src, engage_dest, start_date, end_date):
        """Fetch invoices from the Engage API."""
        invoices = []
        url = f'{self.config["engage_uri"]}/invoicev1/invoiceGroup'
        headers = {
            'x-api-key': engage_src.api_key,
            'businessID': str(engage_src.src_id),
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            invoice_list = response.json().get("data", [])
            self.logger.info(f"Fetched {len(invoice_list)} invoices.")

            for invoice in invoice_list:
                invoice_data = {
                    "contract_idx": contract["contract_idx"],
                    "contract_name": contract["contract_name"],
                    # Add more fields as required based on invoice detail
                }
                invoices.append(invoice_data)

            return invoices
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching invoices: {e}"
            self.logger.error(error_message)
            raise RuntimeError(error_message) from e

    def add_invoice(self, invoice_data):
        """Add invoice to Engage API. Placeholder for implementation."""
        # Logic for adding invoice to Engage API would go here
        pass

# Usage example:
# engage_api = EngageAPI()
# tickets = engage_api.get_tickets(contract, engage_src, engage_dest, start_date, end_date)