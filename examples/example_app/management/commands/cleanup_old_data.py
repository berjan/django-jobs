import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Cleans up old data from the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete data older than this many days'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process at once'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        mode = "DRY RUN" if dry_run else "LIVE"
        self.stdout.write(f"\n[{mode}] Starting cleanup of data older than {days} days...")
        self.stdout.write(f"Cutoff date: {cutoff_date}")
        self.stdout.write(f"Batch size: {batch_size}\n")
        
        # Simulate finding and deleting old records
        total_deleted = 0
        
        for batch in range(3):  # Simulate 3 batches
            # Simulate random number of records in each batch
            records_in_batch = random.randint(50, 150)
            
            self.stdout.write(f"Processing batch {batch + 1}...")
            self.stdout.write(f"  Found {records_in_batch} records to process")
            
            if not dry_run:
                self.stdout.write(f"  Deleting {records_in_batch} records...")
                total_deleted += records_in_batch
            else:
                self.stdout.write(f"  Would delete {records_in_batch} records")
                total_deleted += records_in_batch
            
        self.stdout.write(f"\nCleanup completed!")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN: Would have deleted {total_deleted} records"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {total_deleted} records"))
        
        self.stdout.write(f"Finished at: {timezone.now()}")