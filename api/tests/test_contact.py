import os
import json

from datetime import datetime
from django.test import TestCase
from rest_framework import status

from api.operations import ContactOperations, CsrfOperations
from api.managers import SecretsManager, ConfigManager

class ContactTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

        self.headers = {
            'Authorization': f'Api-Key {self.keys["FIZIT_MASTER_KEY"]}',
            'Content-Type': 'application/json'
        }

        self.contact_ops = ContactOperations(self.headers, self.config)
        self.csrf_ops = CsrfOperations(self.headers, self.config)

    def test_add_list_and_delete_contact(self):
        # Step 1: Add a new contact
        contact_data = {
            "name": "John Doe",
            "email": "johndoe@example.com",
            "company": "Test Company",
            "message": "This is a test message"
        }

        response = self.contact_ops.add_contact(contact_data)
        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Failed to add contact. Status code: {response.status_code}\nResponse: {response.text}")
        else:
            contact_idx = response.json()['contact_idx']
            print(f"Contact added successfully: {response.json()}")

        # Step 2: Retrieve the list of contacts and confirm the one we added exists
        response = self.contact_ops.get_contacts()
        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Failed to retrieve contacts. Status code: {response.status_code}\nResponse: {response.text}")

        contacts = response.json()

        # Assert the contact we added is present in the list
        contact_exists = any(contact['email'] == contact_data['email'] for contact in contacts)
        self.assertTrue(contact_exists, "The contact we added was not found in the list of contacts.")

        print("Contact found in the list.")

        # Step 3: Delete the contact
        csrf_token = self.csrf_ops._get_csrf_token()
        response = self.contact_ops.delete_contact(contact_idx, csrf_token)
        if response.status_code != status.HTTP_204_NO_CONTENT:
            self.fail(f"Failed to delete contact. Status code: {response.status_code}\nResponse: {response.text}")
        else:
            print(f"Contact deleted successfully: {contact_idx}")

        # Step 4: Retrieve the list of contacts and confirm the contact is deleted
        response = self.contact_ops.get_contacts()
        if response.status_code != status.HTTP_200_OK:
            self.fail(f"Failed to retrieve contacts. Status code: {response.status_code}\nResponse: {response.text}")

        contacts_after_deletion = response.json()

        # Assert the contact we deleted is not present in the list anymore
        contact_still_exists = any(contact['contact_idx'] == contact_idx for contact in contacts_after_deletion)
        self.assertFalse(contact_still_exists, "The contact was not deleted successfully.")

        print("Contact deletion validated successfully.")