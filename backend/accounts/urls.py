from django.urls import path
from .views import home, register_citizen

urlpatterns = [
    path("", home, name="home"),
    path("register/", register_citizen, name="register_citizen"),
]