from django import forms
from django.contrib.auth.models import User
from .models import Message

class FriendSearchForm(forms.Form):
    query = forms.CharField(
        label='查找用户',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '输入用户名或邮箱'})
    )

class MessageForm(forms.ModelForm):
    content = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': '输入消息内容...',
            'rows': 3,
        })
    )

    class Meta:
        model = Message
        fields = ['content'] 