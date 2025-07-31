from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.utils import timezone
from croniter import croniter
from .models import CommandSchedule, CommandLog


class CommandScheduleTestCase(TestCase):
    def setUp(self):
        self.schedule = CommandSchedule.objects.create(
            command_name='help',
            active=True,
            schedule_hour='*',
            schedule_minute='*',
            schedule_day='*'
        )

    def test_command_schedule_creation(self):
        self.assertEqual(self.schedule.command_name, 'help')
        self.assertTrue(self.schedule.active)

    def test_run_job(self):
        log_id = self.schedule.run_job()
        log = CommandLog.objects.get(pk=log_id)
        self.assertEqual(log.command_name, 'help')
        self.assertIn(log.status, ['S', 'F'])  # Should be Success or Failure

    def test_get_available_arguments(self):
        args = self.schedule.get_available_arguments()
        self.assertIsInstance(args, list)
    
    def test_cron_interval_validation(self):
        """Test that cron interval expressions are validated correctly"""
        # Test valid interval expressions
        valid_schedules = [
            {'schedule_minute': '*/15', 'schedule_hour': '*', 'schedule_day': '*'},
            {'schedule_minute': '0,30', 'schedule_hour': '*/2', 'schedule_day': '*'},
            {'schedule_minute': '0', 'schedule_hour': '9-17', 'schedule_day': '1-5'},
        ]
        
        for schedule_data in valid_schedules:
            schedule = CommandSchedule(
                command_name='help',
                active=True,
                **schedule_data
            )
            # Should not raise ValidationError
            schedule.clean()
    
    def test_invalid_cron_expressions(self):
        """Test that invalid cron expressions raise ValidationError"""
        invalid_schedules = [
            {'schedule_minute': '60', 'schedule_hour': '*', 'schedule_day': '*'},  # Invalid minute
            {'schedule_minute': '*', 'schedule_hour': '25', 'schedule_day': '*'},  # Invalid hour
            {'schedule_minute': 'invalid', 'schedule_hour': '*', 'schedule_day': '*'},  # Invalid text
        ]
        
        for schedule_data in invalid_schedules:
            schedule = CommandSchedule(
                command_name='help',
                active=True,
                **schedule_data
            )
            with self.assertRaises(ValidationError):
                schedule.clean()
    
    def test_every_15_minutes_schedule(self):
        """Test creating a schedule that runs every 15 minutes"""
        schedule = CommandSchedule.objects.create(
            command_name='test_cron',
            active=True,
            schedule_minute='*/15',
            schedule_hour='*',
            schedule_day='*'
        )
        
        # Test that the cron expression is valid
        cron_expression = f"{schedule.schedule_minute} {schedule.schedule_hour} {schedule.schedule_day} * *"
        cron = croniter(cron_expression)
        
        # Should be able to get next run times
        next_run = cron.get_next()
        self.assertIsNotNone(next_run)


class CommandLogTestCase(TestCase):
    def test_command_log_creation(self):
        log = CommandLog.objects.create(
            command_name='test_command',
            app_name='test_app'
        )
        self.assertEqual(log.status, CommandLog.STATUS_PENDING)
        self.assertIsNotNone(log.started_at)

    def test_set_running(self):
        log = CommandLog.objects.create(command_name='test_command')
        log.set_running()
        self.assertEqual(log.status, CommandLog.STATUS_RUNNING)

    def test_set_success(self):
        log = CommandLog.objects.create(command_name='test_command')
        log.set_success('Success output')
        self.assertEqual(log.status, CommandLog.STATUS_SUCCESS)
        self.assertEqual(log.output, 'Success output')
        self.assertIsNotNone(log.ended_at)
        self.assertIsNotNone(log.duration)

    def test_set_failure(self):
        log = CommandLog.objects.create(command_name='test_command')
        log.set_failure('Error output')
        self.assertEqual(log.status, CommandLog.STATUS_FAILURE)
        self.assertEqual(log.output, 'Error output')
        self.assertIsNotNone(log.ended_at)
        self.assertIsNotNone(log.duration)