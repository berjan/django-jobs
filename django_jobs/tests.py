from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
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