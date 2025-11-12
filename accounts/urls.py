from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='user_register'),
    path('verify/', views.UserRegisterCodeView.as_view(), name='verify_code'),
    path('login/', views.login_view, name='login'),
]