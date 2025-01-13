import logging
from django.test import TestCase
from rest_framework import status
from api.operations import ContactOperations, CsrfOperations
from api.managers import SecretsManager, ConfigManager

from api.utilities.logging import log_info, log_warning, log_error

class ContactTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.logger = logging.getLogger(__name__)

        cls.secrets_manager = SecretsManager()
        cls.config_manager = ConfigManager()

        cls.keys = cls.secrets_manager.load_keys()
        cls.config = cls.config_manager.load_config()

        cls.headers = {
            'Authorization': f'Api-Key {cls.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }
        cls.csrf_ops = CsrfOperations(cls.headers, cls.config)
        cls.csrf_token = cls.csrf_ops.get_csrf_token()

        cls.contact_ops = ContactOperations(cls.headers, cls.config, cls.csrf_token)

        log_info(cls.logger, "Test data initialized successfully.")

    def setUp(self):
        """Prepare for each test."""
        log_info(self.logger, "Setting up test case...")

    def test_add_list_and_delete_contact(self):
        """Test the workflow of adding, listing, and deleting a contact."""
        contact_data = self._create_test_contact()
        self._validate_contact_in_list(contact_data)
        self._delete_and_validate_contact(contact_data)

    def _create_test_contact(self):
        """Add a test contact and validate the response."""
        log_info(self.logger, "Adding a new contact...")

        contact_data = {
            "name": "John Doe",
            "email": "johndoe@example.com",
            "company": "Test Company",
            "message": "This is a test message"
        }

        contact = self.contact_ops.post_contact(contact_data)
        self.assertGreaterEqual(contact["contact_idx"], 0)
        self.assertIsNotNone(contact['contact_idx'], "Contact index is missing in the response.")
        log_info(self.logger, f"Contact added successfully: {contact}")

        return contact

    def _validate_contact_in_list(self, contact_data):
        """Retrieve and validate the added contact in the contact list."""
        log_info(self.logger, "Retrieving list of contacts...")
        contacts = self.contact_ops.get_contacts()
        self.assertGreater(len(contacts), 0)

        log_info(self.logger, "Validating added contact in the list...")
        contact_exists = any(contact['email'] == contact_data['email'] for contact in contacts)
        self.assertTrue(contact_exists, "The added contact was not found in the list.")
        log_info(self.logger, "Contact validation successful.")

    def _delete_and_validate_contact(self, contact_data):
        """Delete the test contact and validate its removal."""
        log_info(self.logger, f"Deleting contact {contact_data['contact_idx']}...")
        response = self.contact_ops.delete_contact(contact_data['contact_idx'])

        self.assertEqual(response, None)
        log_info(self.logger, f"Contact deleted successfully: {contact_data['contact_idx']}")

        log_info(self.logger, "Validating contact deletion...")
        response = self.contact_ops.get_contacts()

        contacts_after_deletion = response
        contact_still_exists = any(contact['contact_idx'] == contact_data['contact_idx'] for contact in contacts_after_deletion)
        self.assertFalse(contact_still_exists, "The contact was not deleted successfully.")
        log_info(self.logger, "Contact deletion validated successfully.")