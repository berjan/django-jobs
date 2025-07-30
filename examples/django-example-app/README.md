# Django Jobs Example Project

This is an example Django 5 project demonstrating how to integrate and use django-jobs.

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
# Username: admin
# Password: (your choice)
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Access the admin at http://localhost:8000/admin/

## Example Management Commands

This project includes three example management commands:

### 1. hello_world
A simple greeting command with arguments:
```bash
python manage.py hello_world --name "Django Jobs" --uppercase
```

### 2. generate_report
Simulates report generation with progress updates:
```bash
python manage.py generate_report --report-type weekly --include-details --email user@example.com
```

### 3. cleanup_old_data
Demonstrates batch processing with dry-run option:
```bash
python manage.py cleanup_old_data --days 60 --dry-run
```

## Configuration

The project is configured with:

```python
# settings.py
DJANGO_JOBS_INCLUDE_APPS = ['example_app', 'django_jobs']
DJANGO_JOBS_EXCLUDE_COMMANDS = ['migrate', 'runserver', 'makemigrations', 'shell', 'startapp', 'startproject', 'test', 'createsuperuser']
DJANGO_JOBS_AUTO_CREATE_SCHEDULES = True
```

## Using Django Jobs Admin

1. Go to http://localhost:8000/admin/django_jobs/commandschedule/
2. If no schedules exist, click "Sync Available Commands"
3. Enable schedules and set their timing (hour, minute, day)
4. Run commands manually using the "Run Now" button
5. View execution logs in the Command Logs section

## Testing Scheduled Jobs

To test the scheduler, run:
```bash
python manage.py run_jobs
```

This will execute any scheduled jobs that match the current time.