from django.urls import path

from auths.api.views import LoginView, RegistrationView

urlpatterns = [
    path("registration/", RegistrationView.as_view()),
    path("login/", LoginView.as_view()),
]
