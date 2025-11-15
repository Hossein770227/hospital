from django.db import models
from django.utils.translation import gettext_lazy as _



class Specialization(models.Model):
    title = models.CharField(_("specialization title"), max_length=100, unique=True)

    class Meta:
        verbose_name = _("Specialization")
        verbose_name_plural = _("Specializations")

    def __str__(self):
        return self.title


class Doctor(models.Model):
    full_name = models.CharField(_("full name"),max_length=100)
    medical_license_number = models.CharField(_("medical license number"), max_length=50,unique=True)
    bio = models.TextField(_("biography"), blank=True)
    specializations = models.ManyToManyField(Specialization, verbose_name=_("specializations"))
    is_active = models.BooleanField( _("is active"), default=True,)
    date_birth =models.DateField(_("date birth"), blank=True, null=True)

    class Meta:
        verbose_name = _("Doctor")
        verbose_name_plural = _("Doctors")
        ordering = ['full_name'] 

    def __str__(self):
        return f"name :{self.full_name} ({self.medical_license_number})"
