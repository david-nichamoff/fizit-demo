import logging
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny  # Import to allow open access

from api.serializers import ContactSerializer
from api.managers import ConfigManager

from api.models import Contact

class ContactViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]  # Apply globally to all methods
    authentication_classes = []  # Disable authentication globally for this view

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.initialized = True

        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

    @extend_schema(
        tags=["Contacts"],
        responses={status.HTTP_200_OK: ContactSerializer(many=True)},
        summary="List Contacts",
        description="Retrieve a list of contacts"
    )
    def list(self, request):
        contacts = Contact.objects.all()
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Contacts"],
        request=ContactSerializer,
        responses={status.HTTP_201_CREATED: ContactSerializer},
        summary="Create Contact",
        description="Create a new contact"
    )
    def add(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save()  # Save the contact first

            # Send email notification
            self._send_contact_notification(contact)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_contact_notification(self, contact):
        """Sends an email notification when a new contact is created."""
        try:
            subject = f"New Contact Created: {contact.name}"
            message = f"Name: {contact.name}\nEmail: {contact.email}\nCompany: {contact.company}\nMessage: {contact.message}"
            recipient_list = self.config["contact_email_list"]

            send_mail(
                subject,
                message,
                'no-reply@fizit.biz',  # From email address
                recipient_list,
                fail_silently=False
            )
            self.logger.info(f"Notification email sent for contact {contact.name}")
        except Exception as e:
            self.logger.error(f"Failed to send notification email: {str(e)}")

    @extend_schema(
        tags=["Contacts"],
        responses={status.HTTP_204_NO_CONTENT: None},
        summary="Delete Contact",
        description="Delete a contact by ID"
    )
    def delete(self, request, contact_idx=None):
        try:
            contact = Contact.objects.get(contact_idx=contact_idx)
            contact.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Contact.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)