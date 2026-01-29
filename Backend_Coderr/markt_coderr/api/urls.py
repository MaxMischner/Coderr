from django.urls import path

from .views import (
    BaseInfoView,
    BusinessProfilesListView,
    CompletedOrderCountView,
    CustomerProfilesListView,
    LoginView,
    OfferDetailRetrieveView,
    OfferDetailUpdateDeleteView,
    OffersListCreateView,
    OrderCountView,
    OrdersListCreateView,
    OrdersUpdateDeleteView,
    ProfileDetailView,
    RegistrationView,
    ReviewsListCreateView,
    ReviewsUpdateDeleteView,
)


urlpatterns = [
    path("profile/<int:pk>/", ProfileDetailView.as_view()),
    path("profiles/business/", BusinessProfilesListView.as_view()),
    path("profiles/customer/", CustomerProfilesListView.as_view()),
    path("offers/", OffersListCreateView.as_view()),
    path("offers/<int:pk>/", OfferDetailUpdateDeleteView.as_view()),
    path("offerdetails/<int:pk>/", OfferDetailRetrieveView.as_view()),
    path("orders/", OrdersListCreateView.as_view()),
    path("orders/<int:pk>/", OrdersUpdateDeleteView.as_view()),
    path("order-count/<int:business_user_id>/", OrderCountView.as_view()),
    path("completed-order-count/<int:business_user_id>/",
         CompletedOrderCountView.as_view()),
    path("reviews/", ReviewsListCreateView.as_view()),
    path("reviews/<int:pk>/", ReviewsUpdateDeleteView.as_view()),
    path("registration/", RegistrationView.as_view()),
    path("login/", LoginView.as_view()),
    path("base-info/", BaseInfoView.as_view()),
]
