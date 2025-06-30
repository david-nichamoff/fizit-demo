import qrcode
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Generate a QR code for a given URL and save it as a PNG file."

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='The URL to encode in the QR code.'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='qrcode.png',
            help='The filename to save the QR code to (default: qrcode.png)'
        )

    def handle(self, *args, **options):
        url = options['url']
        output_file = options['output']

        self.stdout.write(f"Generating QR code for: {url}")
        img = qrcode.make(url)
        img.save(output_file)
        self.stdout.write(self.style.SUCCESS(f"QR code saved to {output_file}"))