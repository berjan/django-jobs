from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Prints hello world with current time'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='World',
            help='Name to greet'
        )
        parser.add_argument(
            '--uppercase',
            action='store_true',
            help='Print in uppercase'
        )

    def handle(self, *args, **options):
        name = options['name']
        message = f"Hello, {name}! The time is {timezone.now()}"
        
        if options['uppercase']:
            message = message.upper()
        
        self.stdout.write(self.style.SUCCESS(message))