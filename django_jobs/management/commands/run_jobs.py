from django.core.management.base import BaseCommand
from django.utils import timezone
from croniter import croniter
from django_jobs.models import CommandSchedule, CommandLog


class Command(BaseCommand):
    help = 'Runs all scheduled management commands'

    def handle(self, *args, **options):
        now = timezone.now()
        
        for command_schedule in CommandSchedule.objects.filter(active=True):
            command_name = command_schedule.command_name
            
            # Build cron expression from individual fields
            cron_expression = f"{command_schedule.schedule_minute} {command_schedule.schedule_hour} {command_schedule.schedule_day} * *"
            
            # Get when this job should have last run (using current time)
            cron = croniter(cron_expression, now)
            should_run_at = cron.get_prev(ret_type=timezone.datetime)
            
            # Check if we already ran this job for the scheduled time
            already_ran = CommandLog.objects.filter(
                command_name=command_name,
                started_at__gte=should_run_at
            ).exists()
            
            # If not already run and within 60 seconds of scheduled time, execute
            if not already_ran and (now - should_run_at).total_seconds() < 60:
                self.stdout.write(self.style.SUCCESS(f"Running command '{command_name}' at {now} (scheduled for {should_run_at})"))
                log_id = command_schedule.run_job()
                self.stdout.write(f"Job started with log ID: {log_id}")