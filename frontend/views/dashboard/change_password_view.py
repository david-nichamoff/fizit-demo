from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required(login_url='/dashboard/login/')
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Prevent logout
            messages.success(request, "✅ Your password was successfully updated.")
            return redirect('dashboard_login')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'dashboard/change_password.html', {'form': form})