# sharing/management/commands/delete_stale_comments.py

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from sharing.models import Comment

class Command(BaseCommand):
    help = 'Deletes comments with PENDING or INAPPROPRIATE status older than 5 minutes.'

    def handle(self, *args, **options):
        cutoff_time = timezone.now() - datetime.timedelta(minutes=5)
        
        stale_comments = Comment.objects.filter(
            status__in=['PENDING', 'INAPPROPRIATE'],
            updated_at__lt=cutoff_time
        )
        
        count = stale_comments.count()
        if count > 0:
            stale_comments.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} stale comments.'))
        else:
            self.stdout.write(self.style.SUCCESS('No stale comments to delete.')) 