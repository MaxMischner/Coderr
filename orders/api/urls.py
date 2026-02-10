from django.urls import path

from orders.api.views import (
    CompletedOrderCountView,
    OrderCountView,
    OrdersListCreateView,
    OrdersUpdateDeleteView,
)

urlpatterns = [
    path("orders/", OrdersListCreateView.as_view()),
    path("orders/<int:pk>/", OrdersUpdateDeleteView.as_view()),
    path("order-count/<int:business_user_id>/", OrderCountView.as_view()),
    path("completed-order-count/<int:business_user_id>/",
         CompletedOrderCountView.as_view()),
]
