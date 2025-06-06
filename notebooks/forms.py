# notebooks/forms.py
from django import forms
from tinymce.widgets import TinyMCE
from .models import Notebook, Category, Tag


class NotebookForm(forms.ModelForm):
    """笔记表单"""

    content = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))

    class Meta:
        model = Notebook
        fields = ['title', 'content', 'category', 'tags', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        # 获取当前用户，以便只显示该用户的分类和标签
        user = kwargs.pop('user', None)
        super(NotebookForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
            self.fields['tags'].queryset = Tag.objects.filter(user=user)

            self.fields['category'].widget.attrs.update({'class': 'form-select'})
            self.fields['tags'].widget.attrs.update({'class': 'form-select'})


class CategoryForm(forms.ModelForm):
    """分类表单"""

    class Meta:
        model = Category
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CategoryForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['parent'].queryset = Category.objects.filter(user=user)


class TagForm(forms.ModelForm):
    """标签表单"""

    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


class CollaborationNotebookForm(NotebookForm):
    """协作笔记编辑表单，包含修改大纲字段"""
    
    edit_summary = forms.CharField(
        label='修改大纲',
        required=True,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '请简要描述本次修改的内容（必填）'
            # 移除 required 属性，避免浏览器HTML5验证冲突
        }),
        help_text='简要说明您做了哪些修改，以便团队成员了解'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 确保修改大纲字段显示在表单中，并且不被TinyMCE处理
        self.fields['edit_summary'].widget.attrs.update({
            'required': True,
            'class': 'form-control',
            'data-no-tinymce': 'true'  # 防止被TinyMCE处理
        })