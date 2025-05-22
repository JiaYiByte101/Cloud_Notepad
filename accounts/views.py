# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile
from .utils import verify_captcha, generate_captcha, generate_captcha_image
import base64


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        captcha = request.POST.get('captcha', '')
        stored_captcha = request.session.get('captcha', '')

        if not verify_captcha(captcha, stored_captcha):
            messages.error(request, '验证码错误，请重新输入')
        elif form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}！')
                # 检查是否是管理员用户
                if user.is_staff or user.is_superuser:
                    return redirect('dashboard:home')
                return redirect('home')
            else:
                messages.error(request, '用户名或密码错误')
    else:
        form = AuthenticationForm()

    # 生成新的验证码
    captcha = generate_captcha()
    request.session['captcha'] = captcha
    captcha_image = generate_captcha_image(captcha)

    return render(request, 'accounts/login.html', {
        'form': form,
        'captcha': captcha,
        'captcha_image': captcha_image
    })

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

def refresh_captcha(request):
    captcha = generate_captcha()
    request.session['captcha'] = captcha
    captcha_image = generate_captcha_image(captcha)
    # 从base64字符串中提取实际的图片数据
    image_data = base64.b64decode(captcha_image.split(',')[1])
    return HttpResponse(image_data, content_type='image/png')