from django.shortcuts import render, redirect
from django.contrib import messages

from frontend.forms.dashboard import CustomUserCreationForm

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Account created. Please wait for access to be granted.')
            return redirect('dashboard_login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'dashboard/register.html', {'form': form})