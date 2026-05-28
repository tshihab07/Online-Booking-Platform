from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import SignupForm, LoginForm, ProfileForm
from .models import CustomUser


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('businesses:dashboard')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Welcome to Bookify! Let\'s set up your business.')
        return redirect('businesses:onboarding')
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('businesses:dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = request.GET.get('next', 'businesses:dashboard')
        return redirect(next_url)
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('core:home')


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
@require_POST
def switch_business(request):
    from businesses.models import Business
    business_id = request.POST.get('business_id')
    business = get_object_or_404(Business, pk=business_id)
    user = request.user
    if str(business_id) in [str(b) for b in (user.businesses or [])]:
        user.active_business_id = str(business_id)
        user.save(update_fields=['active_business_id'])
    return redirect('businesses:dashboard')
