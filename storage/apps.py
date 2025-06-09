from django.apps import AppConfig

class StorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storage'

    def ready(self):
        from django.conf import settings
        from django.core.files.storage import storages
        from importlib import import_module

        if hasattr(settings, 'DEFAULT_FILE_STORAGE'):
            storage_path = settings.DEFAULT_FILE_STORAGE
            module_path, class_name = storage_path.rsplit('.', 1)
            module = import_module(module_path)
            storage_class = getattr(module, class_name)

            # 重新绑定 Django 的 default_storage 实例
            storages._storages.clear()
            storages._storages["default"] = storage_class()

            import sys
            print(f"✅ 强制绑定 default_storage 为 {storage_class}", file=sys.stderr)
