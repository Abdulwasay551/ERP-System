"""
Loads a full company-data snapshot (as produced by GET /api/core/export-snapshot/) into
the current database - the desktop app's first-run pairing step (Phase 3 of the desktop
app plan). Thin CLI wrapper around core.snapshot.import_snapshot_data(); the real
desktop app will call that function directly after downloading the export over HTTP,
not shell out to this command - this exists for manual testing/verification and as a
recovery tool.

Usage: python manage.py import_snapshot --file snapshot.json
"""
import json

from django.core.management.base import BaseCommand, CommandError

from core.snapshot import import_snapshot_data


class Command(BaseCommand):
    help = 'Import a full company-data snapshot exported from /api/core/export-snapshot/.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='Path to the exported snapshot JSON file.')
        parser.add_argument(
            '--expected-company-id', type=int, default=None,
            help='Refuse to import if the snapshot contains a different company id than this.',
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
            raise CommandError("Snapshot file is missing the top-level 'objects' key.")

        self.stdout.write(f"Importing snapshot exported at {payload.get('exported_at', '?')} "
                           f"for company_id={payload.get('company_id', '?')} "
                           f"({len(objects)} objects)...")
        try:
            count = import_snapshot_data(objects, expected_company_id=options['expected_company_id'])
        except ValueError as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS(f'Imported {count} objects.'))
