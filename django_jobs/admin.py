import json

from django import forms
from django.contrib import admin, messages
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
    actions = ['run_selected_jobs', 'view_command_args']
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
                        # Save original args
                        orig_args = command.arguments
                        # Set temporary args
                        command.arguments = args
                        # Run job asynchronously
                        log_id = command.run_job_async()
                        log_ids.append(log_id)
                        # Restore original args
                        command.arguments = orig_args
                        command.save()
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


class CommandLogAdmin(admin.ModelAdmin):
    list_display = ('command_name', 'app_name',
                    'status', 'started_at', 'ended_at', 'duration')
    list_filter = ('started_at', 'app_name', 'status',)
    readonly_fields = ('command_name', 'app_name', 'status',
                       'started_at', 'ended_at', 'duration', 'output')
    search_fields = ('command_name', 'app_name', 'output')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(CommandSchedule, CommandScheduleAdmin)
admin.site.register(CommandLog, CommandLogAdmin)