import random
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from .models import MyUser, OtpCode
from .forms import UserRegisterForm, VerifyCodeForm
from utils import send_otp_code
from django.utils.translation import gettext as _


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
                return redirect('store:product_list')

            messages.error(request, _('The entered code is incorrect.'))
            return redirect('accounts:verify_code')

        return render(request, 'accounts/verify_code.html', {'form': form})