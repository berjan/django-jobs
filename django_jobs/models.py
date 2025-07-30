import json
import os
import shlex
import subprocess
import threading
import time
import traceback
from datetime import datetime
from io import StringIO

from django.core.management import get_commands, load_command_class
from django.db import connection, models
from django.utils import timezone

# Extract the available management commands
COMMAND_CHOICES = sorted([(command, command)
                         for command in get_commands().keys()])


class CommandSchedule(models.Model):
    command_name = models.CharField(
        max_length=255,
        unique=True,
        choices=COMMAND_CHOICES,
    )
    app_name = models.CharField(max_length=255, null=True, blank=True)
    schedule_hour = models.CharField(
        max_length=5, default='*', help_text='Use * for every hour')
    schedule_minute = models.CharField(
        max_length=5, default='*', help_text='Use * for every minute')
    schedule_day = models.CharField(
        max_length=5, default='*', help_text='Use * for every day')
    active = models.BooleanField(default=False)
    arguments = models.JSONField(default=dict, blank=True,
                                 help_text='JSON dictionary of arguments to pass to the command')

    class Meta:
        verbose_name = "Command Schedule"
        verbose_name_plural = "Command Schedules"

    @staticmethod
    def run_jobs(queryset):
        """Run multiple jobs asynchronously"""
        for schedule in queryset:
            schedule.run_job_async()
        return len(queryset)

    def _stream_output(self, process, log_id):
        """Stream and capture output from a running process in real-time"""
        # Buffers for stdout and stderr
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()

        # Last update time to avoid too frequent DB updates
        last_update = time.time()

        try:
            # Read from stdout and stderr while the process is running
            with process.stdout as stdout, process.stderr as stderr:
                # Set stdout and stderr to non-blocking mode
                import fcntl
                import os

                # Set non-blocking for stdout
                flags_stdout = fcntl.fcntl(stdout.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(stdout.fileno(), fcntl.F_SETFL,
                            flags_stdout | os.O_NONBLOCK)

                # Set non-blocking for stderr
                flags_stderr = fcntl.fcntl(stderr.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(stderr.fileno(), fcntl.F_SETFL,
                            flags_stderr | os.O_NONBLOCK)

                # While the process is still running
                while process.poll() is None:
                    # Try to read from stdout
                    try:
                        stdout_chunk = stdout.read()
                        if stdout_chunk:
                            decoded = stdout_chunk.decode('utf-8')
                            stdout_buffer.write(decoded)
                    except (IOError, BlockingIOError):
                        pass

                    # Try to read from stderr
                    try:
                        stderr_chunk = stderr.read()
                        if stderr_chunk:
                            decoded = stderr_chunk.decode('utf-8')
                            stderr_buffer.write(decoded)
                    except (IOError, BlockingIOError):
                        pass

                    # Update the log if enough time has passed (avoid too frequent updates)
                    current_time = time.time()
                    if current_time - last_update > 1.0:  # Update at most once per second
                        try:
                            log = CommandLog.objects.get(pk=log_id)
                            # Update the output in the database
                            stdout_content = stdout_buffer.getvalue()
                            stderr_content = stderr_buffer.getvalue()
                            output = f"STDOUT (in progress):\n{stdout_content}\n\nSTDERR (in progress):\n{stderr_content}"
                            log.output = output
                            log.save(update_fields=['output'])
                            last_update = current_time
                        except Exception as e:
                            print(f"Error updating log: {str(e)}")

                    # Don't hog the CPU
                    time.sleep(0.1)

                # Final read after process completes
                stdout_content = stdout_buffer.getvalue() + stdout.read().decode('utf-8')
                stderr_content = stderr_buffer.getvalue() + stderr.read().decode('utf-8')

                return stdout_content, stderr_content

        except Exception as e:
            error_text = f"Error reading process output: {str(e)}\n{traceback.format_exc()}"
            print(error_text)
            return stdout_buffer.getvalue(), stderr_buffer.getvalue() + f"\n{error_text}"

    def _execute_command(self, command, log_id):
        """Execute the command in a separate thread with real-time output"""
        try:
            # Get a fresh log object
            log = CommandLog.objects.get(pk=log_id)
            log.set_running()
            log.output = f"Starting command: {command}\n"
            log.save()

            try:
                # Start process with pipe for stdout and stderr
                process = subprocess.Popen(
                    shlex.split(command),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=1,  # Line buffered
                    universal_newlines=False  # Binary mode
                )

                # Stream and capture output
                stdout_content, stderr_content = self._stream_output(process, log_id)

                # Get the final exit code
                return_code = process.poll()

                # Process output
                output = f"STDOUT:\n{stdout_content}\n\nSTDERR:\n{stderr_content}"

                # Update the log with final results
                log = CommandLog.objects.get(pk=log_id)

                if return_code == 0:
                    log.set_success(output)
                else:
                    log.set_failure(output)

            except Exception as e:
                error_text = f"Error running command: {str(e)}\n{traceback.format_exc()}"
                log.set_failure(error_text)

        except Exception as e:
            # Handle any exceptions
            error_text = f"Error executing command: {str(e)}\n{traceback.format_exc()}"
            try:
                log = CommandLog.objects.get(pk=log_id)
                log.set_failure(error_text)
            except Exception as inner_e:
                # If we can't update the log, log to console
                print(f"CRITICAL ERROR: Could not update log {log_id}: {str(inner_e)}")
                print(error_text)

    def run_job(self):
        """Create log entry and run job synchronously"""
        log = CommandLog(
            command_name=self.command_name,
            app_name=self.app_name,
        )
        log.save()

        try:
            # Start with the base command
            command = f'python manage.py {self.command_name}'

            # Add arguments from JSON field
            if self.arguments:
                args_list = []
                for key, value in self.arguments.items():
                    if value is True:
                        # Handle boolean flags (just the flag, no value)
                        args_list.append(f'--{key}')
                    elif value is not False:  # Don't add if False
                        # Handle all other arguments
                        args_list.append(f'--{key}={value}')

                if args_list:
                    command += ' ' + ' '.join(args_list)

            result = subprocess.run(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            output = result.stdout.decode('utf-8') + result.stderr.decode('utf-8')

            if result.returncode == 0:
                log.set_success(output)
            else:
                log.set_failure(output)
        except Exception as e:
            output = str(e)
            log.set_failure(output)

        return log.pk

    def run_job_async(self):
        """Run the job asynchronously in a separate thread"""
        # Create the log entry first
        log = CommandLog(
            command_name=self.command_name,
            app_name=self.app_name,
        )
        log.save()

        # Build the command
        command = f'python manage.py {self.command_name}'

        # Add arguments from JSON field
        if self.arguments:
            args_list = []
            for key, value in self.arguments.items():
                if value is True:
                    # Handle boolean flags
                    args_list.append(f'--{key}')
                elif value is not False:  # Don't add if False
                    # Handle all other arguments
                    args_list.append(f'--{key}={value}')

            if args_list:
                command += ' ' + ' '.join(args_list)

        # Start a new thread to execute the command
        thread = threading.Thread(
            target=self._execute_command,
            args=(command, log.pk)
        )
        thread.daemon = True  # Make the thread a daemon so it doesn't block program exit
        thread.start()

        return log.pk

    def get_available_arguments(self):
        """
        Introspect the command to get available arguments
        """
        try:
            app_name = get_commands()[self.command_name]
            command_class = load_command_class(app_name, self.command_name)

            # Get parser arguments
            parser = command_class.create_parser('manage.py', self.command_name)

            # Extract argument info
            arguments = []
            for action in parser._actions:
                if action.dest != 'help':  # Skip the help action
                    arg_info = {
                        'name': action.dest,
                        'help': action.help,
                        'required': action.required,
                        'default': action.default if action.default != '==SUPPRESS==' else None,
                    }

                    # Add type information if available
                    if hasattr(action, 'type') and action.type:
                        arg_info['type'] = action.type.__name__

                    # Add choices if available
                    if hasattr(action, 'choices') and action.choices:
                        arg_info['choices'] = list(action.choices)

                    arguments.append(arg_info)

            return arguments
        except Exception as e:
            return [{'error': str(e)}]

    def __str__(self):
        return self.command_name


class CommandLog(models.Model):
    STATUS_PENDING = 'P'
    STATUS_RUNNING = 'R'
    STATUS_SUCCESS = 'S'
    STATUS_FAILURE = 'F'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILURE, 'Failure'),
    )

    command_name = models.CharField(max_length=255)
    app_name = models.CharField(max_length=255, null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    output = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        verbose_name = "Command Log"
        verbose_name_plural = "Command Logs"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.command_name} ({self.started_at})"

    def set_running(self):
        self.status = self.STATUS_RUNNING
        self.save()

    def end(self):
        self.ended_at = timezone.now()
        self.duration = self.ended_at - self.started_at
        self.save()

    def set_success(self, output):
        self.status = self.STATUS_SUCCESS
        self.output = output
        self.end()

    def set_failure(self, output):
        self.status = self.STATUS_FAILURE
        self.output = output
        self.end()