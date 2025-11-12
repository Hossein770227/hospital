import pytz
import random
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext as _
from datetime import timedelta
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.views import View

from .forms import PhoneLoginForm, UserRegisterForm, VerifyCodeForm
from .models import OtpCode,MyUser
from .forms import ForgotPasswordForm, VerifyCodeForm, ResetPasswordForm
from utils import send_otp_code


class UserRegisterView(View):
    form_class = UserRegisterForm

    def get(self, request):
        form = self.form_class()
        return render(request, 'accounts/user_register.html', {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']

            otp = OtpCode.objects.filter(phone_number=phone).last()
            if otp and not otp.is_expired():
                messages.error(request, _('We already sent you a code. Please wait.'))
                return redirect('accounts:verify_code')

            OtpCode.objects.filter(phone_number=phone).delete()

            random_code = random.randint(1000, 9999)
            send_otp_code(phone, random_code)

            OtpCode.objects.create(phone_number=phone, code=random_code)

            request.session['user_registration_info'] = {
                'phone_number': phone,
                'full_name': form.cleaned_data['full_name'],
                'password': form.cleaned_data['password2'],
            }

            messages.success(request, _('Verification code sent successfully.'))
            return redirect('accounts:verify_code')

        return render(request, 'accounts/user_register.html', {'form': form})


class UserRegisterCodeView(View):
    form_class = VerifyCodeForm

    def get(self, request):
        user_session = request.session.get('user_registration_info')
        if not user_session:
            messages.error(request, _('Registration information not found.'))
            return redirect('accounts:user_register')
        form = self.form_class()
        return render(request, 'accounts/verify_code.html', {'form': form})

    def post(self, request):
        user_session = request.session.get('user_registration_info')
        if not user_session:
            messages.error(request, _('Registration information not found.'))
            return redirect('accounts:user_register')

        form = self.form_class(request.POST)
        if form.is_valid():
            code_instance = OtpCode.objects.filter(phone_number=user_session['phone_number']).last()

            if not code_instance:
                messages.error(request, _('No code was found for this phone number.'))
                return redirect('accounts:user_register')

            if code_instance.is_expired():
                code_instance.delete()
                messages.error(request, _('The OTP code has expired.'))
                return redirect('accounts:user_register')

            cd = form.cleaned_data
            if str(cd['code']) == str(code_instance.code):
                user = MyUser.objects.create_user(
                    phone_number=user_session['phone_number'],
                    full_name=user_session['full_name'],
                    password=user_session['password']
                )
                code_instance.delete()
                del request.session['user_registration_info']
                messages.success(request, _('You have successfully registered.'))
                login(request, user)
                return redirect('main:hospital')

            messages.error(request, _('The entered code is incorrect.'))
            return redirect('accounts:verify_code')

        return render(request, 'accounts/verify_code.html', {'form': form})

def login_view(request):
    if request.method == "GET":
        form = PhoneLoginForm()
        return render(request, "accounts/login.html", {"form": form})

    form = PhoneLoginForm(request.POST)
    if not form.is_valid():
        messages.warning(request, _("Invalid phone number or password."))
        return render(request, "accounts/login.html", {"form": form})

    user = form.get_user()
    login(request, user)
    messages.success(request, _("You have successfully logged in."))

    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("main:hospital")

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.error(request, _('You have successfully logged out.'))
        return redirect('main:hospital')

    return redirect('main:hospital')


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  
            messages.success(request, _('Your password was changed successfully.'))
            return redirect('main:hospital')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'accounts/password_change.html', {'form': form})






def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            User = get_user_model()

            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                messages.error(request, _("This phone number is not registered in the system."))
                return render(request, 'accounts/forgot_password.html', {'form': form})

            latest_otp = OtpCode.objects.filter(phone_number=phone_number).order_by('-date_time_created').first()
            if latest_otp and (timezone.now() - latest_otp.date_time_created).total_seconds() < 120:
                messages.error(request, _("Please wait a moment before requesting a new OTP."))
                return render(request, 'accounts/forgot_password.html', {'form': form})

            OtpCode.objects.filter(phone_number=phone_number).delete()
            random_code = random.randint(1000, 9999)
            send_otp_code(phone_number, random_code)
            OtpCode.objects.create(phone_number=phone_number, code=random_code)

            request.session['reset_phone'] = str(phone_number)
            messages.success(request, _("A verification code has been sent to your phone number."))
            return redirect(reverse('accounts:verify_code_forgot_password'))
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def verify_code_forgot_password(request):
    reset_phone = request.session.get('reset_phone')
    if not reset_phone:
        messages.error(request, _("Session expired. Please start over."))
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']

            try:
                code_instance = OtpCode.objects.get(phone_number=reset_phone)
            except OtpCode.DoesNotExist:
                messages.error(request, _('No OTP code found for this phone number.'))
                return redirect('accounts:forgot_password')

            now = timezone.now()
            expired_time = code_instance.date_time_created + timedelta(minutes=2)

            if now > expired_time:
                code_instance.delete()
                messages.error(request, _('The OTP code has expired. Please request a new one.'))
                return redirect('accounts:forgot_password')

            if str(code) == str(code_instance.code):
                code_instance.delete() 
                messages.success(request, _('Code verified successfully.'))
                return redirect('accounts:reset_password')
            else:
                messages.error(request, _('The entered code is incorrect.'))
                return redirect('accounts:verify_code_forgot_password')
    else:
        form = VerifyCodeForm()

    return render(request, 'accounts/verify_code_forgot_password.html', {'form': form})


def reset_password(request):
    reset_phone = request.session.get('reset_phone')
    if not reset_phone:
        messages.error(request, _('Please start from the password recovery step.'))
        return redirect('accounts:forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            User = get_user_model()

            try:
                user = User.objects.get(phone_number=reset_phone)
            except User.DoesNotExist:
                messages.error(request, _("User not found."))
                return render(request, 'accounts/reset_password.html', {'form': form})

            user.password = make_password(new_password)
            user.save()

            request.session.pop('reset_phone', None)
            request.session.pop('reset_code', None)

            update_session_auth_hash(request, user)
            messages.success(request, _("Your password has been successfully changed."))
            return redirect('accounts:login')
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form})
