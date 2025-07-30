import json
import threading

from django import forms
from django.contrib import admin, messages
from django.core.management import call_command
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import CommandLog, CommandSchedule


class CommandArgsForm(forms.Form):
    """Form for providing command arguments"""
    arguments = forms.JSONField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'cols': 80}),
        help_text='Enter arguments as JSON: {"arg1": "value1", "arg2": true}'
    )


class CommandScheduleAdmin(admin.ModelAdmin):
    list_display = ('command_name', 'app_name', 'schedule_hour',
                    'schedule_minute', 'schedule_day', 'active', 'view_arguments_btn', 'run_job_btn')
    list_filter = ('app_name', 'active')
    list_editable = ('active', 'schedule_hour',
                     'schedule_minute', 'schedule_day')
    actions = ['run_selected_jobs', 'view_command_args', 'sync_jobs']
    readonly_fields = ('display_available_arguments',)
    fieldsets = (
        (None, {
            'fields': ('command_name', 'app_name', 'active')
        }),
        ('Schedule', {
            'fields': ('schedule_hour', 'schedule_minute', 'schedule_day')
        }),
        ('Arguments', {
            'fields': ('arguments', 'display_available_arguments')
        }),
    )

    def view_arguments_btn(self, obj):
        """Add button to view available arguments"""
        return format_html(
            '<a href="{}" class="button">View Arguments</a>',
            reverse('admin:view_command_args', args=[obj.pk])
        )
    view_arguments_btn.short_description = "Arguments"

    def run_job_btn(self, obj):
        """Add button to run job manually"""
        return format_html(
            '<a href="{}?id={}" class="button" style="background-color: #28a745; color: white;">Run Now</a>',
            reverse('admin:django_jobs_commandschedule_run_with_args'),
            obj.pk
        )
    run_job_btn.short_description = "Run"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'run-with-args/',
                self.admin_site.admin_view(self.run_with_args),
                name='django_jobs_commandschedule_run_with_args',
            ),
            path(
                'view_command_args/<int:command_id>/',
                self.admin_site.admin_view(self.view_command_args_view),
                name='view_command_args',
            ),
            path(
                'run_single_job/<int:job_id>/',
                self.admin_site.admin_view(self.run_single_job),
                name='run_single_job',
            ),
            path(
                'job_status/<int:log_id>/',
                self.admin_site.admin_view(self.job_status),
                name='job_status',
            ),
        ]
        return custom_urls + urls

    def run_selected_jobs(self, request, queryset):
        """Run job with optional arguments"""
        selected = request.POST.getlist('_selected_action')

        # Construct the URL with IDs as GET parameters
        base_url = reverse('admin:django_jobs_commandschedule_run_with_args')
        id_params = '&'.join([f'id={pk}' for pk in selected])
        url = f"{base_url}?{id_params}"

        return HttpResponseRedirect(url)
    run_selected_jobs.short_description = 'Run selected jobs manually'

    def run_with_args(self, request):
        """View for providing arguments before running jobs"""
        # Get command IDs from either POST or GET
        command_ids = request.POST.getlist(
            '_selected_action') or request.GET.getlist('id')

        # If no command IDs were found, redirect back to the changelist
        if not command_ids and 'apply' not in request.POST:
            self.message_user(request, "No commands selected",
                              level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:django_jobs_commandschedule_changelist'))

        # Get the commands
        commands = CommandSchedule.objects.filter(pk__in=command_ids)

        if 'apply' in request.POST:
            # Process the form submission
            form = CommandArgsForm(request.POST)
            if form.is_valid():
                # If arguments provided, temporarily update the command objects
                args = form.cleaned_data.get('arguments')
                log_ids = []

                # Run the commands with provided args asynchronously
                for command in commands:
                    if args:
                        # Create log with custom arguments
                        log = CommandLog(
                            command_name=command.command_name,
                            app_name=command.app_name,
                            arguments=args,
                        )
                        log.save()
                        
                        # Build command with custom args
                        temp_command = CommandSchedule(
                            command_name=command.command_name,
                            app_name=command.app_name,
                            arguments=args,
                        )
                        # Execute in thread
                        command_str = CommandSchedule.build_command_string(command.command_name, args)
                        
                        thread = threading.Thread(
                            target=command._execute_command,
                            args=(command_str, log.pk)
                        )
                        thread.daemon = True
                        thread.start()
                        log_ids.append(log.pk)
                    else:
                        log_id = command.run_job_async()
                        log_ids.append(log_id)

                # Redirect to job status page or logs list
                if len(log_ids) == 1:
                    return render(request, 'admin/job_status.html', {
                        'title': f'Running job: {commands[0].command_name}',
                        'log_id': log_ids[0],
                        'status_url': reverse('admin:job_status', args=[log_ids[0]]),
                        'log_url': reverse('admin:django_jobs_commandlog_change', args=[log_ids[0]]),
                        'logs_list_url': reverse('admin:django_jobs_commandlog_changelist'),
                    })
                else:
                    self.message_user(
                        request, f"Started {len(log_ids)} jobs. Check job logs for status.")
                    return HttpResponseRedirect(reverse('admin:django_jobs_commandlog_changelist'))
        else:
            # Display the form for entering arguments
            form = CommandArgsForm()

        command_args = {}
        # Get available arguments for all selected commands
        for command in commands:
            command_args[command.command_name] = command.get_available_arguments()

        return render(
            request,
            'admin/run_with_args.html',
            {
                'commands': commands,
                'command_args': command_args,
                'form': form,
                'title': 'Run commands with arguments',
            }
        )

    def view_command_args_view(self, request, command_id):
        """View for displaying available command arguments"""
        command = CommandSchedule.objects.get(pk=command_id)
        args = command.get_available_arguments()

        return render(
            request,
            'admin/view_command_args.html',
            {
                'command': command,
                'args': args,
                'title': f'Available arguments for {command.command_name}'
            }
        )

    def run_single_job(self, request, job_id):
        """Run a single job directly"""
        job = get_object_or_404(CommandSchedule, pk=job_id)
        log_id = job.run_job_async()

        return HttpResponseRedirect(
            reverse('admin:job_status', args=[log_id])
        )

    def job_status(self, request, log_id):
        """AJAX endpoint to check job status"""
        try:
            log = CommandLog.objects.get(pk=log_id)
            status_data = {
                'status': log.get_status_display(),
                'status_code': log.status,
                'started_at': log.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                'ended_at': log.ended_at.strftime('%Y-%m-%d %H:%M:%S') if log.ended_at else None,
                'duration': str(log.duration) if log.duration else None,
                'has_output': bool(log.output),
            }

            # Only include a preview of the output to keep the response small
            if log.output:
                output_preview = log.output[:500]
                if len(log.output) > 500:
                    output_preview += '...'
                status_data['output_preview'] = output_preview

            return JsonResponse(status_data)

        except Exception as e:
            import traceback
            error_msg = f"Error retrieving job status: {str(e)}\n{traceback.format_exc()}"

            return JsonResponse({
                'error': error_msg,
                'status': 'Error',
                'status_code': 'F'
            }, status=500)

    def display_available_arguments(self, obj):
        """Display available arguments in the admin form"""
        args = obj.get_available_arguments()

        if not args:
            return "No arguments available"

        html = "<table>"
        html += "<tr><th>Argument</th><th>Description</th><th>Required</th><th>Default</th></tr>"

        for arg in args:
            if 'error' in arg:
                return f"Error getting arguments: {arg['error']}"

            name = arg.get('name', '')
            help_text = arg.get('help', '')
            required = "Yes" if arg.get('required') else "No"
            default = arg.get('default', 'None')

            html += f"<tr><td>{name}</td><td>{help_text}</td><td>{required}</td><td>{default}</td></tr>"

        html += "</table>"

        return format_html(html)
    display_available_arguments.short_description = "Available Arguments"
    
    def sync_jobs(self, request, queryset):
        """Sync available commands with database"""
        try:
            from io import StringIO
            import sys
            
            # Capture output
            output = StringIO()
            old_stdout = sys.stdout
            sys.stdout = output
            
            # Call the sync_jobs command with --create-missing flag
            result = call_command('sync_jobs', '--create-missing')
            
            sys.stdout = old_stdout
            command_output = output.getvalue()
            
            # Parse the output to show a user-friendly message
            if 'Created' in command_output:
                # Extract the number of created schedules
                import re
                match = re.search(r'Created (\d+) new CommandSchedule entries', command_output)
                if match:
                    count = match.group(1)
                    self.message_user(
                        request, 
                        f"Successfully synchronized commands. Created {count} new schedule(s).",
                        messages.SUCCESS
                    )
                else:
                    self.message_user(request, "Commands synchronized successfully.", messages.SUCCESS)
            else:
                self.message_user(request, "All commands already have schedules.", messages.INFO)
                
        except Exception as e:
            self.message_user(
                request,
                f"Error synchronizing commands: {str(e)}",
                messages.ERROR
            )
    
    sync_jobs.short_description = "Sync available commands"


class CommandLogAdmin(admin.ModelAdmin):
    list_display = ('command_name', 'app_name',
                    'status', 'started_at', 'ended_at', 'duration', 'has_arguments')
    list_filter = ('started_at', 'app_name', 'status',)
    readonly_fields = ('command_name', 'app_name', 'status',
                       'started_at', 'ended_at', 'duration', 'display_arguments', 'display_run_again_button', 'output')
    search_fields = ('command_name', 'app_name', 'output')
    actions = ['run_jobs_manually']
    
    fieldsets = (
        (None, {
            'fields': ('command_name', 'app_name', 'status')
        }),
        ('Execution Details', {
            'fields': ('started_at', 'ended_at', 'duration', 'display_arguments', 'display_run_again_button')
        }),
        ('Output', {
            'fields': ('output',),
            'classes': ('collapse',)
        }),
    )
    
    def has_arguments(self, obj):
        """Show if command had arguments"""
        return bool(obj.arguments)
    has_arguments.boolean = True
    has_arguments.short_description = "Args"
    
    def display_arguments(self, obj):
        """Display arguments in a readable format"""
        if not obj.arguments:
            return "No arguments"
        
        # Format JSON safely for HTML display
        json_str = json.dumps(obj.arguments, indent=2)
        
        return format_html(
            '<pre style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; margin: 0;">{}</pre>',
            json_str
        )
    display_arguments.short_description = "Arguments Used"
    
    def display_run_again_button(self, obj):
        """Display a button to run the command again with the same arguments"""
        if not obj:
            return ""
        
        # Find or create a CommandSchedule for this command
        try:
            schedule = CommandSchedule.objects.get(command_name=obj.command_name)
        except CommandSchedule.DoesNotExist:
            # Create a temporary schedule
            schedule, created = CommandSchedule.objects.get_or_create(
                command_name=obj.command_name,
                defaults={
                    'app_name': obj.app_name,
                    'active': False,
                }
            )
        
        # Build URL with pre-filled arguments
        base_url = reverse('admin:django_jobs_commandschedule_run_with_args')
        url = f"{base_url}?id={schedule.pk}"
        
        # If there are arguments, we need to pass them via session or encode them
        # For now, we'll create a temporary schedule with the arguments
        if obj.arguments:
            # Store the arguments temporarily in the schedule
            schedule.arguments = obj.arguments
            schedule.save()
        
        return format_html(
            '<a href="{}" class="button" style="background-color: #417690; color: white; padding: 10px 20px; '
            'text-decoration: none; display: inline-block; margin: 5px 0;">Run Again with Same Arguments</a>',
            url
        )
    display_run_again_button.short_description = "Actions"
    
    def run_jobs_manually(self, request, queryset):
        """Run commands manually with arguments"""
        # Get unique command names from the selected logs
        command_names = list(queryset.values_list('command_name', flat=True).distinct())
        
        # Find or create temporary CommandSchedule objects for the run_with_args view
        schedule_ids = []
        for command_name in command_names:
            try:
                # Try to find existing schedule
                schedule = CommandSchedule.objects.get(command_name=command_name)
                schedule_ids.append(str(schedule.pk))
            except CommandSchedule.DoesNotExist:
                # Create a temporary schedule for commands that don't have one
                # We'll use get_or_create to avoid duplicates
                schedule, created = CommandSchedule.objects.get_or_create(
                    command_name=command_name,
                    defaults={
                        'app_name': queryset.filter(command_name=command_name).first().app_name,
                        'active': False,  # Keep it inactive
                    }
                )
                schedule_ids.append(str(schedule.pk))
        
        # Redirect to the run_with_args view with the schedule IDs
        base_url = reverse('admin:django_jobs_commandschedule_run_with_args')
        id_params = '&'.join([f'id={pk}' for pk in schedule_ids])
        url = f"{base_url}?{id_params}"
        
        return HttpResponseRedirect(url)
    
    run_jobs_manually.short_description = "Run selected commands manually"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(CommandSchedule, CommandScheduleAdmin)
admin.site.register(CommandLog, CommandLogAdmin)