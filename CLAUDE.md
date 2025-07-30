# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django Jobs is a reusable Django app for managing and scheduling Django management commands. It provides:
- Admin interface for scheduling commands with cron-like syntax
- Real-time command execution monitoring
- Command execution history and output tracking
- Support for command arguments via JSON
- Multi-tenant support (optional, via django-tenants)

## Commands

### Installation & Setup
```bash
# Install package (for development)
pip install -e .

# Apply migrations in target Django project
python manage.py migrate django_jobs

# Sync available commands
python manage.py sync_jobs
```

### Management Commands
- `python manage.py run_jobs` - Execute all scheduled jobs based on current time
- `python manage.py sync_jobs` - Synchronize available Django management commands
- `python manage.py delete_logs` - Clean up old command execution logs

### Development
```bash
# Run tests
python manage.py test django_jobs

# Package distribution
python setup.py sdist bdist_wheel
```

## Architecture

### Core Models (django_jobs/models.py)

**CommandSchedule**: Stores scheduled commands with cron-like scheduling
- Uses `schedule_hour`, `schedule_minute`, `schedule_day` fields (use '*' for "every")
- `arguments` field stores JSON dict of command arguments
- `run_job()` - Synchronous execution
- `run_job_async()` - Asynchronous execution in separate thread with real-time output streaming

**CommandLog**: Tracks command execution history
- Status tracking: PENDING → RUNNING → SUCCESS/FAILURE
- Real-time output capture via subprocess with non-blocking I/O
- Duration tracking and timestamping

### Admin Interface (django_jobs/admin.py)

Provides comprehensive admin UI with:
- Inline command execution with custom arguments
- Real-time job status monitoring via AJAX
- Available arguments introspection for each command
- Bulk job execution support

### Key Implementation Details

1. **Command Execution**: Uses subprocess.Popen with real-time output streaming
   - Non-blocking I/O for stdout/stderr capture
   - Updates CommandLog output every second during execution
   - Thread-based async execution for non-blocking admin operations

2. **Command Discovery**: Leverages Django's `get_commands()` and `load_command_class()`
   - Automatically discovers all available management commands
   - Introspects command arguments via argparse

3. **Scheduling Logic**: Simple cron-like matching in `run_jobs` command
   - Matches current time against schedule fields
   - Supports wildcard (*) for "every" interval

## Integration Requirements

To use django-jobs in a Django project:
1. Add 'django_jobs' to INSTALLED_APPS
2. Include django_jobs URLs if using custom views
3. Run migrations to create database tables
4. Configure scheduled jobs via Django admin