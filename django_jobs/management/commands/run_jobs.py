from django.core.management.base import BaseCommand
from django.utils import timezone
from django_jobs.models import CommandSchedule


class Command(BaseCommand):
    help = 'Runs all scheduled management commands'

    def handle(self, *args, **options):
        now = timezone.now()
        
        for command_schedule in CommandSchedule.objects.filter(active=True):
            command_name = command_schedule.command_name
            schedule_hour = command_schedule.schedule_hour
            schedule_minute = command_schedule.schedule_minute
            schedule_day = command_schedule.schedule_day

            if (schedule_hour == '*' or str(now.hour) == schedule_hour) and \
               (schedule_minute == '*' or str(now.minute) == schedule_minute) and \
               (schedule_day == '*' or str(now.day) == schedule_day):
                self.stdout.write(self.style.SUCCESS(f"Running command '{command_name}' at {now}"))
                log_id = command_schedule.run_job()
                self.stdout.write(f"Job started with log ID: {log_id}")