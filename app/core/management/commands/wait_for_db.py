"""
Django command to wait for database connection
"""
import time

from psycopg2 import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for database connection"""
    def handle(self, *args, **options):
        self.stdout.write('waiting for database...')
        db_up = False
        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write('Database unavailable, will wait 1 sec')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))


        pass