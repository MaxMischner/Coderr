from django.urls import path

from profiles.api.views import (
    BusinessProfilesListView,
    CustomerProfilesListView,
    ProfileDetailView,
)

urlpatterns = [
    path("profile/<int:pk>/", ProfileDetailView.as_view()),
    path("profiles/business/", BusinessProfilesListView.as_view()),
    path("profiles/customer/", CustomerProfilesListView.as_view()),
]
