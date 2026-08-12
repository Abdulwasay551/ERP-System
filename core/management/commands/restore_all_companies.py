"""
Disaster-recovery restore (Phase B of the desktop app plan): seeds a brand-new,
empty backend from a full multi-company backup file (as produced by GET
/api/core/export-all-companies-backup/, or the desktop app's "Download Backup"
button). CLI-only, deliberately never exposed as a web/API action - see
core.snapshot.import_all_companies_snapshot()'s own docstring for why: a genuine
"production's database is gone" scenario means seeding a database with no User rows
yet to authenticate as, so this can only ever be run with direct server/database
access.

Usage: python manage.py restore_all_companies --file backup.json
       python manage.py restore_all_companies --file backup.json --allow-nonempty
"""
import json

from django.core.management.base import BaseCommand, CommandError

from core.snapshot import import_all_companies_snapshot


class Command(BaseCommand):
    help = 'Disaster-recovery restore: seed a brand-new, empty database from a full backup file.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='Path to the backup JSON file.')
        parser.add_argument(
            '--allow-nonempty', action='store_true',
            help='Override the empty-database guard. Only use this if you specifically '
                 'intend to merge a backup into a database that already has company data - '
                 'the ordinary disaster-recovery case is always an empty target.',
        )

    def handle(self, *args, **options):
        path = options['file']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'No such file: {path}')
        except json.JSONDecodeError as e:
            raise CommandError(f'{path} is not valid JSON: {e}')

        objects = payload.get('objects')
        if objects is None:
            raise CommandError("Backup file is missing the top-level 'objects' key.")

        self.stdout.write(
            f"Restoring backup exported at {payload.get('exported_at', '?')} "
            f"({len(objects)} objects across {len(payload.get('company_ids', []))} compan"
            f"{'y' if len(payload.get('company_ids', [])) == 1 else 'ies'})..."
        )
        try:
            count = import_all_companies_snapshot(objects, allow_nonempty=options['allow_nonempty'])
        except ValueError as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS(f'Restored {count} objects.'))
