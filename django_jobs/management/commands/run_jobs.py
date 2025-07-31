from django.core.management.base import BaseCommand
from django.utils import timezone
from croniter import croniter
from django_jobs.models import CommandSchedule


class Command(BaseCommand):
    help = 'Runs all scheduled management commands'

    def handle(self, *args, **options):
        now = timezone.now()
        
        for command_schedule in CommandSchedule.objects.filter(active=True):
            command_name = command_schedule.command_name
            
            # Build cron expression from individual fields
            cron_expression = f"{command_schedule.schedule_minute} {command_schedule.schedule_hour} {command_schedule.schedule_day} * *"
            
            # Check if the current time matches the cron schedule
            cron = croniter(cron_expression, now.replace(second=0, microsecond=0))
            previous_run = cron.get_prev()
            next_run = cron.get_next()
            
            # If the previous run time is within the last minute, execute the job
            if now.timestamp() - previous_run < 60:
                self.stdout.write(self.style.SUCCESS(f"Running command '{command_name}' at {now}"))
                log_id = command_schedule.run_job()
                self.stdout.write(f"Job started with log ID: {log_id}")