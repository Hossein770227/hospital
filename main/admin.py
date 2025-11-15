from django.contrib import admin
from . models import Specialization, Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display =['full_name', 'medical_license_number', 'is_active', 'date_birth']
    list_filter = ['full_name', 'is_active', 'date_birth']
    search_fields = ['full_name', 'medical_license_number', 'specializations']
    ordering = ['specializations']

  
    
