from django.urls import path

from base_info.api.views import BaseInfoView

urlpatterns = [
    path("base-info/", BaseInfoView.as_view()),
]
