from django.core.management.base import BaseCommand
from django.utils import timezone
from collaboration.models import CollaborationLock


class Command(BaseCommand):
    help = '清理过期的协作锁'

    def handle(self, *args, **options):
        # 删除所有过期的锁
        expired_locks = CollaborationLock.objects.filter(
            expires_at__lt=timezone.now()
        )
        
        count = expired_locks.count()
        expired_locks.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'成功清理了 {count} 个过期的协作锁')
        ) 