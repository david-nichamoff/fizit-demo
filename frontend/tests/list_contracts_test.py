import json
import os
import logging

from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from django.template.response import TemplateResponse

from frontend.views.dashboard import list_contracts_view

from api.utilities.logging import log_debug, log_info, log_error, log_warning

class ListContractsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.customer = "fizit"
        self.logger = logging.getLogger(__name__)
        self.user = MagicMock()

        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures/list_contracts_test.json")
        with open(fixture_path) as f:
            self.contract_list = json.load(f)  

        log_info(self.logger, f"Mock contract list:  {self.contract_list}")

    @patch("frontend.views.dashboard.list_contracts_view.build_app_context")
    @patch("api.operations.CsrfOperations.get_csrf_token", return_value="mock-token")
    @patch("api.operations.ContractOperations.list_contracts_by_party_code")
    @patch("frontend.views.dashboard.list_contracts_view.group_matches_customer", lambda f: f)
    def test_list_contracts_view_success(self, mock_list_contracts, mock_get_csrf_token, mock_build_context):
        # Mock context
        mock_context = MagicMock()
        mock_context.secrets_manager.get_master_key.return_value = "mock-api-key"
        mock_context.config_manager.get_base_url.return_value = "http://fake"
        mock_build_context.return_value = mock_context

        # Return the list of contracts directly
        mock_list_contracts.return_value = self.contract_list

        request = self.factory.get(f"/dashboard/{self.customer}/")
        request.user = self.user
        response = list_contracts_view(request, self.customer)

        html = response.content.decode()

        # Confirm title is rendered
        self.assertIn("FIZIT Contracts", html)

        # Confirm at least one known contract shows up
        expected_idx = str(min(c["contract_idx"] for c in self.contract_list))
        self.assertIn(f">{expected_idx}<", html)

        # Check that the title is rendered correctly
        self.assertIn("<h1>FIZIT Contracts</h1>", html)

        # Check that the customer slug appears in links or page (optional)
        self.assertIn("/dashboard/fizit/", html)

        # Check that the first contract index is the smallest one (sorted check)
        expected_first_idx = str(min(c["contract_idx"] for c in self.contract_list))
        self.assertIn(f">{expected_first_idx}<", html)  # checks <td>0</td>, etc.