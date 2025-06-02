from django.shortcuts import render, redirect
from JobJab.core.forms import CleanUserCreationForm
from django.contrib import messages


def register(request):
    if request.method == 'POST':
        form = CleanUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now login.')
            return redirect('login')
    else:
        form = CleanUserCreationForm()

    return render(request, 'core/register.html', {'form': form})

def login(request):
    pass

def logout(request):
    pass