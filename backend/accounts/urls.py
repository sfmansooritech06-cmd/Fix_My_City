from django.urls import path
from .views import register_citizen


urlpatterns = [
    path("register/", register_citizen, name="register_citizen"),
]