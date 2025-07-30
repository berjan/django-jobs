from django.conf import settings
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
        
        # Get settings for filtering
        include_apps = getattr(settings, 'DJANGO_JOBS_INCLUDE_APPS', None)
        exclude_commands = getattr(settings, 'DJANGO_JOBS_EXCLUDE_COMMANDS', [])
        auto_create = getattr(settings, 'DJANGO_JOBS_AUTO_CREATE_SCHEDULES', False)
        
        # If create_missing is not explicitly set, use the settings value
        if not create_missing and auto_create:
            create_missing = True
        
        # Filter commands based on settings
        filtered_commands = {}
        for cmd_name, app_name in all_commands.items():
            # Skip excluded commands
            if cmd_name in exclude_commands:
                continue
                
            # If include_apps is specified, only include commands from those apps
            if include_apps and app_name not in include_apps:
                continue
                
            filtered_commands[cmd_name] = app_name
        
        # Get existing command schedules
        existing_schedules = set(CommandSchedule.objects.values_list('command_name', flat=True))
        
        # Find missing commands
        missing_commands = set(filtered_commands.keys()) - existing_schedules
        
        if missing_commands:
            self.stdout.write(self.style.WARNING(f"Found {len(missing_commands)} commands without schedules:"))
            for cmd in sorted(missing_commands):
                self.stdout.write(f"  - {cmd} (from {all_commands[cmd]})")
                
            if create_missing:
                created_count = 0
                for cmd in missing_commands:
                    CommandSchedule.objects.create(
                        command_name=cmd,
                        app_name=filtered_commands[cmd],
                        active=False  # Create inactive by default
                    )
                    created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created {created_count} new CommandSchedule entries"))
            else:
                created_count = 0
        else:
            self.stdout.write(self.style.SUCCESS("All commands have schedules"))
        
        # Check for obsolete schedules (commands that no longer exist)
        obsolete_schedules = existing_schedules - set(filtered_commands.keys())
        if obsolete_schedules:
            self.stdout.write(self.style.WARNING(f"\nFound {len(obsolete_schedules)} obsolete schedules:"))
            for cmd in sorted(obsolete_schedules):
                self.stdout.write(f"  - {cmd}")
            self.stdout.write("Consider removing these obsolete schedules manually.")
        
