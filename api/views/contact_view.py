import logging
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny

from api.serializers import ContactSerializer
from api.managers import ConfigManager
from api.models import Contact

from api.mixins.shared import ValidationMixin
from api.utilities.logging import log_info, log_error, log_warning
from api.utilities.validation import is_valid_list, is_valid_integer


class ContactViewSet(viewsets.ViewSet, ValidationMixin):
    """
    ViewSet for managing Contact operations.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

    @extend_schema(
        tags=["Contacts"],
        responses={status.HTTP_200_OK: ContactSerializer(many=True)},
        summary="List Contacts",
        description="Retrieve a list of all contacts."
    )
    def list(self, request):
        """Retrieve and return all contacts."""
        log_info(self.logger, "Fetching all contacts.")
        try:
            contacts = Contact.objects.all()
            serializer = ContactSerializer(contacts, many=True)
            log_info(self.logger, f"Retrieved {len(contacts)} contacts.")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            log_error(self.logger, f"Unexpected error while fetching contacts: {e}")
            return Response({"error": f"Unexpected error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contacts"],
        request=ContactSerializer,
        responses={status.HTTP_201_CREATED: ContactSerializer},
        summary="Create Contact",
        description="Create a new contact and send a notification email."
    )
    def create(self, request):
        """Create a new contact and send an email notification."""
        log_info(self.logger, "Attempting to create a new contact.")
        try:
            serializer = ContactSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Save the contact
            contact = serializer.save()
            log_info(self.logger, f"Successfully created contact {contact.name}.")
            self._send_contact_notification(contact)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            log_error(self.logger, f"Unexpected error while creating contact: {e}")
            return Response({"error": f"Unexpected error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=["Contacts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Contact",
        description="Delete a contact by its unique ID."
    )
    def delete(self, request, contact_idx=None):
        """Delete a specific contact by its ID."""
        log_info(self.logger, f"Attempting to delete contact with ID {contact_idx}.")
        try:
            # Validate contact_idx
            if not is_valid_integer(contact_idx):
                raise RuntimeError

            # Fetch and delete the contact
            contact = Contact.objects.get(contact_idx=contact_idx)
            contact.delete()
            log_info(self.logger, f"Successfully deleted contact with ID {contact_idx}.")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Contact.DoesNotExist:
            log_error(self.logger, f"Contact with ID {contact_idx} not found.")
            return Response({"error": "Contact not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_error(self.logger, f"Unexpected error while deleting contact {contact_idx}: {e}")
            return Response({"error": f"Unexpected error {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _send_contact_notification(self, contact):
        """
        Sends an email notification for a newly created contact.
        """
        log_info(self.logger, f"Preparing to send email notification for contact {contact.name}.")
        try:
            subject = f"New Contact Created: {contact.name}"
            message = (
                f"Name: {contact.name}\n"
                f"Email: {contact.email}\n"
                f"Company: {contact.company}\n"
                f"Message: {contact.message}"
            )
            recipient_list = self.config.get("contact_email_list", [])

            # Validate recipient list
            is_valid_list(recipient_list, allow_empty=False)

            send_mail(
                subject,
                message,
                'no-reply@fizit.biz',
                recipient_list,
                fail_silently=False
            )
            log_info(self.logger, f"Notification email successfully sent for contact {contact.name}.")
        except Exception as e:
            log_error(self.logger, f"Failed to send notification email for contact {contact.name}: {e}")