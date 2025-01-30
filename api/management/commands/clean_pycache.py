import shutil
import pathlib

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Cleans pycache directories, its good to do this periodically'


    def handle(self, *args, **options):

        for pycache in pathlib.Path(".").rglob("__pycache__"):
            shutil.rmtree(pycache)

        self.stdout.write(self.style.SUCCESS(f'Cleaned pycache'))