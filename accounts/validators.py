import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


phone_regex = re.compile(r"^(?:\+98|0)9\d{9}$")

def validate_iranian_phone(value):

    if not phone_regex.match(value):
        raise ValidationError(_('Enter a valid Iranian cellphone number.'))
    

    if value.startswith('+98'):
        value = '0' + value[3:]
    return value
