# Generated migration file for django_jobs

import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CommandSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command_name', models.CharField(max_length=255, unique=True)),
                ('app_name', models.CharField(blank=True, max_length=255, null=True)),
                ('schedule_hour', models.CharField(default='*', help_text='Use * for every hour', max_length=5)),
                ('schedule_minute', models.CharField(default='*', help_text='Use * for every minute', max_length=5)),
                ('schedule_day', models.CharField(default='*', help_text='Use * for every day', max_length=5)),
                ('active', models.BooleanField(default=False)),
                ('arguments', models.JSONField(blank=True, default=dict, help_text='JSON dictionary of arguments to pass to the command')),
            ],
            options={
                'verbose_name': 'Command Schedule',
                'verbose_name_plural': 'Command Schedules',
            },
        ),
        migrations.CreateModel(
            name='CommandLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('command_name', models.CharField(max_length=255)),
                ('app_name', models.CharField(blank=True, max_length=255, null=True)),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration', models.DurationField(blank=True, null=True)),
                ('output', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('P', 'Pending'), ('R', 'Running'), ('S', 'Success'), ('F', 'Failure')], default='P', max_length=1)),
            ],
            options={
                'verbose_name': 'Command Log',
                'verbose_name_plural': 'Command Logs',
                'ordering': ['-started_at'],
            },
        ),
    ]