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

3. (Optional) Configure settings in your `settings.py`:

```python
# Only include commands from specific apps (if not set, all apps are included)
DJANGO_JOBS_INCLUDE_APPS = ['example_app', 'myapp']

# Exclude specific commands from being synced
DJANGO_JOBS_EXCLUDE_COMMANDS = ['migrate', 'runserver', 'makemigrations', 'shell']

# Automatically create schedules when running sync_jobs
DJANGO_JOBS_AUTO_CREATE_SCHEDULES = True
```

## Usage

### Admin Interface

The app provides an admin interface for:
- Creating and managing command schedules
- Running commands manually with custom arguments
- Viewing command execution logs
- Real-time monitoring of running jobs
- Syncing available commands using the "Sync available commands" action

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

## Deployment

To run scheduled jobs in production, you need to execute `run_jobs` periodically. Here are three options:

### Option 1: Crontab (Recommended)
Add to your crontab (`crontab -e`):
```bash
# Run every minute
* * * * * cd /path/to/project && /path/to/venv/bin/python manage.py run_jobs
```

### Option 2: Systemd Timer
Create `/etc/systemd/system/django-jobs.service`:
```ini
[Unit]
Description=Django Jobs Runner

[Service]
Type=oneshot
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python manage.py run_jobs
User=www-data
```

Create `/etc/systemd/system/django-jobs.timer`:
```ini
[Unit]
Description=Run Django Jobs every minute

[Timer]
OnCalendar=*:0/1
Persistent=true

[Install]
WantedBy=timers.target
```

Enable with:
```bash
sudo systemctl enable --now django-jobs.timer
```

### Option 3: Celery Beat
If you're already using Celery, create a periodic task that calls the `run_jobs` management command.

## Example Project

Check out the [example project](examples/django-example-app/) to see django-jobs in action. The example demonstrates:
- Integration with a Django 5 project
- Sample management commands with various argument types
- Configuration best practices
- Admin interface usage

To run the example:
```bash
cd examples/django-example-app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## License

MIT License