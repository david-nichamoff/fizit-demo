import logging
from django.core.management.base import BaseCommand
from django.db import connection

from api.utilities.logging import log_info, log_error, log_warning

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Truncate a specified table by deleting all records and resetting the primary key sequence.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--table',
            type=str,
            required=True,
            help='Name of the table to truncate'
        )

    def handle(self, *args, **kwargs):
        table_name = kwargs['table']

        try:
            with connection.cursor() as cursor:
                # Count records before deletion
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count_before = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"Records before truncation: {count_before}"))

                # Delete all rows
                cursor.execute(f"DELETE FROM {table_name};")

                # Reset the primary key sequence (SQLite-specific)
                cursor.execute("DELETE FROM sqlite_sequence WHERE name=%s;", [table_name])

                # Count records after deletion
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count_after = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"Records after truncation: {count_after}"))

                self.stdout.write(self.style.SUCCESS(f"Successfully truncated table: {table_name}"))

        except Exception as e:
            log_error(logger, f"Error truncating table {table_name}: {e}")
            self.stderr.write(self.style.ERROR(f"Error truncating table {table_name}: {e}"))