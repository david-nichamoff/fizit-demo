from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from unittest.mock import patch, MagicMock

from api.utilities.bootstrap import build_app_context

class ViewContractTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="fizit", password="fizitpass")
        group = Group.objects.create(name="fizit")
        self.user.groups.add(group)
        self.client.login(username="fizit", password="fizitpass")

        self.contract_idx = 1
        self.contract_type = "purchase"
        self.url = reverse("view_contract", kwargs={"customer": "fizit"}) + f"?contract_idx={self.contract_idx}&contract_type={self.contract_type}"

    def build_mock_context(self):
        mock = MagicMock()
        mock.config_manager.get_base_url.return_value = "http://fake"
        mock.secrets_manager.get_master_key.return_value = "mock-api-key"
        mock.domain_manager.get_banks.return_value = []
        mock.form_manager.get_contract_form.return_value = lambda **kwargs: MagicMock()
        mock.form_manager.get_settlement_form.return_value = None
        mock.api_manager.get_settlement_api.return_value = False
        return mock

    @patch("frontend.views.dashboard.view_contract_view.build_app_context")
    @patch("api.operations.ContractOperations.get_contract")
    def test_get_view_contract_page_success(self, mock_get_contract, mock_context):
        mock_context.return_value = self.build_mock_context()
        mock_get_contract.return_value = {"contract_idx": 1, "contract_type": "purchase", "funding_instr": {}, "deposit_instr": {}, "transact_logic": {}}

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/view_purchase_contract.html")

    @patch("frontend.views.dashboard.view_contract_view.build_app_context")
    @patch("api.operations.ArtifactOperations.post_artifacts")
    def test_post_upload_artifact_success(self, mock_post_artifacts, mock_context):
        mock_context.return_value = self.build_mock_context()
        mock_post_artifacts.return_value = {"count": 1}

        response = self.client.post(self.url, data={
            "form_type": "artifacts",
            "artifact_url": "https://example.com/artifact.pdf"
        }, follow=True)

        self.assertContains(response, "Artifact uploaded successfully.")

    @patch("frontend.views.dashboard.view_contract_view.generate_contract_report")
    @patch("frontend.views.dashboard.view_contract_view.build_app_context")
    @patch("api.operations.ContractOperations.get_contract")
    def test_post_generate_report_success(self, mock_get_contract, mock_context, mock_report):
        mock_context.return_value = self.build_mock_context()
        mock_get_contract.return_value = {
            "contract_name": "Test Contract",
            "transact_logic": {},
            "funding_instr": {},
            "deposit_instr": {}
        }
        mock_report.return_value = b"%PDF-1.4 dummy content"

        response = self.client.post(self.url, data={"form_type": "generate_report"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(b"%PDF", response.content)

    @patch("frontend.views.dashboard.view_contract_view.build_app_context")
    @patch("api.operations.ContractOperations.get_contract")
    def test_post_execute_logic(self, mock_get_contract, mock_context):
        mock_context.return_value = self.build_mock_context()
        mock_get_contract.return_value = {
            "contract_type": "purchase",
            "contract_idx": 1,
            "transact_logic": {"*": [{"var": "price"}, {"var": "barrels"}]},
            "funding_instr": {},
            "deposit_instr": {}
        }

        response = self.client.post(self.url, data={
            "form_type": "execute_logic",
            "var_price": "10",
            "var_barrels": "5",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Result")
