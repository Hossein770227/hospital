from django.shortcuts import render
from django.views.generic import TemplateView


class Hospital(TemplateView):
    template_name = 'main/main_page.html'
