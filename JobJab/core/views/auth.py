from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from JobJab.core.forms import CleanUserCreationForm, CleanLoginForm


class RegisterView(View):
    template_name = 'core/register.html'

    def get(self, request):
        form = CleanUserCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CleanUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now login.')
            return redirect('login')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    template_name = 'core/login.html'

    def get(self, request):
        form = CleanLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CleanLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user)
                if user.is_staff:
                    return redirect('custom_admin_home')
                return redirect('home')
        messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def get(self, request):
        auth_logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect('home')