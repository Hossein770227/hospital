from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from .validators import validate_iranian_phone
from .models import MyUser


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirm password"), widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ['phone_number', 'full_name']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password1') and cd.get('password2') and cd['password1'] != cd['password2']:
            raise ValidationError(_("Passwords do not match."))
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(help_text=_("You can change the password using this <a href='../password/'>form</a>."))

    class Meta:
        model = MyUser
        fields = ['phone_number', 'full_name', 'password', 'last_login']


class UserRegisterForm(forms.Form):
    full_name = forms.CharField(label=_('Full name'), max_length=100, required=True)
    phone = forms.CharField(
        label=_('Phone number'),
        max_length=11,
        required=True,
        validators=[validate_iranian_phone]
    )
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Confirm password'), widget=forms.PasswordInput)

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if MyUser.objects.filter(phone_number=phone).exists():
            raise ValidationError(_('This phone number already exists.'))
        return phone

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password1') and cd.get('password2') and cd['password1'] != cd['password2']:
            raise ValidationError(_("Passwords do not match."))
        return cd['password2']


class VerifyCodeForm(forms.Form):
    code = forms.IntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(999999)],
        label=_("Verification code")
    )


class ForgotPasswordForm(forms.Form):
    phone_number = forms.CharField(
        label=_('Phone number'),
        max_length=11,
        required=True,
        validators=[validate_iranian_phone]
    )


class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(widget=forms.PasswordInput, label=_("New password"))
    new_password2 = forms.CharField(widget=forms.PasswordInput, label=_("Confirm new password"))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("The passwords must match."))

        return cleaned_data


class PhoneLoginForm(forms.Form):
    phone_number = forms.CharField(label=_("Phone number"), max_length=13)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    def clean(self):
        phone_number = self.cleaned_data.get("phone_number")
        password = self.cleaned_data.get("password")

        if phone_number and password:
            self.user = authenticate(phone_number=phone_number, password=password)
            if self.user is None:
                raise forms.ValidationError(_("Invalid phone number or password"))
        return self.cleaned_data

    def get_user(self):
        return getattr(self, "user", None)