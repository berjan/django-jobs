# Django Jobs

A reusable Django app for managing and scheduling management commands.

## Features

- Schedule Django management commands to run at specific times
- Track command execution history and output
- Admin interface for managing scheduled jobs
- Support for command arguments
- Real-time output streaming for long-running commands
- Multi-tenant support (optional)

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/berjan/django-jobs.git
```

Or add to your requirements.txt:

```
git+https://github.com/berjan/django-jobs.git
```

For a specific branch or tag:

```bash
pip install git+https://github.com/berjan/django-jobs.git@main
pip install git+https://github.com/berjan/django-jobs.git@v0.1.0
```

For development installation (editable):

```bash
pip install -e git+https://github.com/berjan/django-jobs.git#egg=django-jobs
```

## Configuration

1. Add `django_jobs` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'django_jobs',
    ...
]
```

2. Run migrations:

```bash
python manage.py migrate django_jobs
```

## Usage

### Admin Interface

The app provides an admin interface for:
- Creating and managing command schedules
- Running commands manually with custom arguments
- Viewing command execution logs
- Real-time monitoring of running jobs

### Management Commands

The app includes several management commands:
- `run_jobs`: Run all scheduled jobs
- `sync_jobs`: Synchronize available commands
- `delete_logs`: Clean up old command logs

### Scheduling Jobs

Jobs can be scheduled using cron-like syntax:
- Use `*` for "every" (e.g., every hour, every minute)
- Use specific numbers for exact times

Example:
- Hour: `14`, Minute: `30`, Day: `*` = Run at 2:30 PM every day
- Hour: `*`, Minute: `0`, Day: `*` = Run every hour on the hour

## Multi-tenant Support

If you're using django-tenants, the app includes commands for tenant-specific execution:
- `tenant_run_jobs`
- `tenant_execute_jobs`

## License

MIT License