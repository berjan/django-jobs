from django.core.management import get_commands
from django.core.management.base import BaseCommand
from django_jobs.models import CommandSchedule


class Command(BaseCommand):
    help = 'Synchronize available commands with CommandSchedule model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create CommandSchedule entries for missing commands',
        )

    def handle(self, *args, **options):
        create_missing = options['create_missing']
        
        # Get all available commands
        all_commands = get_commands()
        
        # Get existing command schedules
        existing_schedules = set(CommandSchedule.objects.values_list('command_name', flat=True))
        
        # Find missing commands
        missing_commands = set(all_commands.keys()) - existing_schedules
        
        if missing_commands:
            self.stdout.write(self.style.WARNING(f"Found {len(missing_commands)} commands without schedules:"))
            for cmd in sorted(missing_commands):
                self.stdout.write(f"  - {cmd} (from {all_commands[cmd]})")
                
            if create_missing:
                created_count = 0
                for cmd in missing_commands:
                    CommandSchedule.objects.create(
                        command_name=cmd,
                        app_name=all_commands[cmd],
                        active=False  # Create inactive by default
                    )
                    created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created {created_count} new CommandSchedule entries"))
        else:
            self.stdout.write(self.style.SUCCESS("All commands have schedules"))
        
        # Check for obsolete schedules (commands that no longer exist)
        obsolete_schedules = existing_schedules - set(all_commands.keys())
        if obsolete_schedules:
            self.stdout.write(self.style.WARNING(f"\nFound {len(obsolete_schedules)} obsolete schedules:"))
            for cmd in sorted(obsolete_schedules):
                self.stdout.write(f"  - {cmd}")
            self.stdout.write("Consider removing these obsolete schedules manually.")