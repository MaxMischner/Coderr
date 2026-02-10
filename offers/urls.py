from django.urls import path

from offers.views import (
    OfferDetailRetrieveView,
    OfferDetailUpdateDeleteView,
    OffersListCreateView,
)

urlpatterns = [
    path("offers/", OffersListCreateView.as_view()),
    path("offers/<int:pk>/", OfferDetailUpdateDeleteView.as_view()),
    path("offerdetails/<int:pk>/", OfferDetailRetrieveView.as_view()),
]
