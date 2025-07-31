# Migration for croniter support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_jobs', '0002_commandlog_arguments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commandschedule',
            name='schedule_day',
            field=models.CharField(default='*', help_text='Cron expression for day: * for every day, */7 for every 7 days, 1-31 for specific day, 1,15 for multiple values', max_length=20),
        ),
        migrations.AlterField(
            model_name='commandschedule',
            name='schedule_hour',
            field=models.CharField(default='*', help_text='Cron expression for hour: * for every hour, */2 for every 2 hours, 0-23 for specific hour, 9-17 for range', max_length=20),
        ),
        migrations.AlterField(
            model_name='commandschedule',
            name='schedule_minute',
            field=models.CharField(default='*', help_text='Cron expression for minute: * for every minute, */15 for every 15 minutes, 0-59 for specific minute, 0,30 for multiple values', max_length=20),
        ),
    ]