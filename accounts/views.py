from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        student_id = request.POST.get('student_id')
        phone_number = request.POST.get('phone_number')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'accounts/register.html')

        if student_id and User.objects.filter(student_id=student_id).exists():
            messages.error(request, 'Student ID already registered.')
            return render(request, 'accounts/register.html')

        new_user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password1,
            role=User.ROLE_STUDENT,
            student_id=student_id if student_id else None,
            phone_number=phone_number if phone_number else None,
        )

        login(request, new_user)
        messages.success(request, f'Welcome, {new_user.first_name}! Your account has been created.')
        return redirect('dashboard')

    return render(request, 'accounts/register.html')


@login_required
def dashboard_redirect_view(request):
    if request.user.is_student():
        return redirect('student_dashboard')
    elif request.user.is_tutor():
        return redirect('tutor_dashboard')
    elif request.user.is_admin_user() or request.user.is_staff:
        return redirect('/admin/')
    return redirect('login')
