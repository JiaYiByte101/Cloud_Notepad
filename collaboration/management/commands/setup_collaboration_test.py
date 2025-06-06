from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notebooks.models import Notebook
from collaboration.models import CollaborationProject, CollaborationMember
from friends.models import Friendship
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '创建协作项目测试数据'

    def handle(self, *args, **options):
        try:
            # 获取或创建测试用户
            owner, _ = User.objects.get_or_create(
                username='test_owner',
                defaults={'email': 'owner@test.com'}
            )
            owner.set_password('test123')
            owner.save()
            
            member1, _ = User.objects.get_or_create(
                username='test_member1',
                defaults={'email': 'member1@test.com'}
            )
            member1.set_password('test123')
            member1.save()
            
            member2, _ = User.objects.get_or_create(
                username='test_member2',
                defaults={'email': 'member2@test.com'}
            )
            member2.set_password('test123')
            member2.save()
            
            # 创建好友关系
            Friendship.objects.get_or_create(user=owner, friend=member1)
            Friendship.objects.get_or_create(user=member1, friend=owner)
            Friendship.objects.get_or_create(user=owner, friend=member2)
            Friendship.objects.get_or_create(user=member2, friend=owner)
            
            # 创建测试笔记
            notebook1 = Notebook.objects.create(
                title='测试协作笔记1',
                content='这是一个用于测试协作功能的笔记。',
                user=owner
            )
            
            notebook2 = Notebook.objects.create(
                title='测试协作笔记2',
                content='这是另一个协作笔记。',
                user=owner
            )
            
            # 创建协作项目
            project = CollaborationProject.objects.create(
                name='测试协作项目',
                description='用于测试群聊和修改通知功能',
                owner=owner
            )
            
            # 添加笔记到项目
            project.notebooks.add(notebook1, notebook2)
            
            # 创建成员邀请
            member1_invitation = CollaborationMember.objects.create(
                project=project,
                user=member1,
                role='editor',
                status='pending',
                invited_by=owner
            )
            
            member2_invitation = CollaborationMember.objects.create(
                project=project,
                user=member2,
                role='viewer',
                status='pending',
                invited_by=owner
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'测试数据创建成功！\n'
                f'项目创建者: {owner.username} (密码: test123)\n'
                f'成员1: {member1.username} (密码: test123)\n'
                f'成员2: {member2.username} (密码: test123)\n'
                f'协作项目: {project.name}\n'
                f'请登录成员账号接受邀请以创建群聊'
            ))
            
        except Exception as e:
            logger.error(f"创建测试数据时出错: {str(e)}")
            self.stdout.write(self.style.ERROR(f'创建测试数据失败: {str(e)}')) 