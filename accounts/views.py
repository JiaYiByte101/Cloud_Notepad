# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'欢迎加入云记事本，{username}！您的账户已创建成功。')
            return redirect('accounts:login')
        else:
            messages.error(request, '注册过程中出现错误，请检查下面的提示信息。')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    # 确保用户有一个profile对象
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    
    # 传递上下文信息给模板
    context = {
        'user': request.user,
        'profile': request.user.profile
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '太好了！您的个人资料已成功更新。')
            return redirect('accounts:profile')
        else:
            messages.error(request, '更新个人资料时出现错误，请检查下面的提示信息。')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def logout_confirm(request):
    if request.method == 'POST':
        messages.success(request, '您已成功退出登录。期待您的再次访问！')
        logout(request)
        return redirect('home')
    return render(request, 'accounts/logout.html')