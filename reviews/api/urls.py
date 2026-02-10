from django.urls import path

from reviews.api.views import ReviewsListCreateView, ReviewsUpdateDeleteView

urlpatterns = [
    path("reviews/", ReviewsListCreateView.as_view()),
    path("reviews/<int:pk>/", ReviewsUpdateDeleteView.as_view()),
]
