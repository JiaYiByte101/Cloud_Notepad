# sharing/forms.py

from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    """评论表单"""

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '发表您的评论...'})
        }