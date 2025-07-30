from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_jobs.models import CommandLog


class Command(BaseCommand):
    help = 'Delete old command logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete logs older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        logs_to_delete = CommandLog.objects.filter(started_at__lt=cutoff_date)
        count = logs_to_delete.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"No logs older than {days} days found."))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN: Would delete {count} logs older than {days} days"))
            for log in logs_to_delete[:10]:  # Show first 10
                self.stdout.write(f"  - {log.command_name} ({log.started_at})")
            if count > 10:
                self.stdout.write(f"  ... and {count - 10} more")
        else:
            logs_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} logs older than {days} days"))