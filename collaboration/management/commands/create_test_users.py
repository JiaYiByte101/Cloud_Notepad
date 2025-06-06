from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notebooks.models import Notebook, Category
from collaboration.models import CollaborationProject, CollaborationMember


class Command(BaseCommand):
    help = '创建测试用户和协作项目用于验证锁机制'

    def handle(self, *args, **options):
        # 创建测试用户
        users = []
        for i in range(1, 4):  # 创建3个测试用户
            username = f'testuser{i}'
            email = f'testuser{i}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'测试用户{i}',
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'创建用户: {username} (密码: testpass123)')
            else:
                self.stdout.write(f'用户已存在: {username}')
            
            users.append(user)
        
        # 为第一个用户创建测试笔记
        user1 = users[0]
        category, _ = Category.objects.get_or_create(
            name='测试分类',
            user=user1
        )
        
        notebook, created = Notebook.objects.get_or_create(
            title='协作测试笔记',
            user=user1,
            defaults={
                'content': '<p>这是一个用于测试协作锁机制的笔记。</p><p>请尝试多个用户同时编辑此笔记来验证锁机制。</p>',
                'category': category,
                'is_public': False
            }
        )
        
        if created:
            self.stdout.write(f'创建测试笔记: {notebook.title}')
        
        # 创建协作项目
        project, created = CollaborationProject.objects.get_or_create(
            name='锁机制测试项目',
            owner=user1,
            defaults={
                'description': '用于测试协作锁机制的项目'
            }
        )
        
        if created:
            project.notebooks.add(notebook)
            self.stdout.write(f'创建协作项目: {project.name}')
        
        # 添加其他用户为项目成员
        for user in users[1:]:
            member, created = CollaborationMember.objects.get_or_create(
                project=project,
                user=user,
                defaults={
                    'role': 'editor',
                    'status': 'accepted'
                }
            )
            
            if created:
                self.stdout.write(f'添加成员: {user.username} (编辑者)')
        
        self.stdout.write(
            self.style.SUCCESS('\n测试环境创建完成！')
        )
        self.stdout.write('验证步骤：')
        self.stdout.write('1. 使用不同浏览器登录不同的测试用户')
        self.stdout.write('2. 访问协作项目中的测试笔记')
        self.stdout.write('3. 尝试同时编辑来验证锁机制')
        self.stdout.write(f'4. 笔记ID: {notebook.id}')
        self.stdout.write(f'5. 项目ID: {project.id}') 