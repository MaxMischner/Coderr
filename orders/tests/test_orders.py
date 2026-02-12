from copy import deepcopy

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


ORDER_KEYS = {
    "id",
    "customer_user",
    "business_user",
    "title",
    "revisions",
    "delivery_time_in_days",
    "price",
    "features",
    "offer_type",
    "status",
    "created_at",
    "updated_at",
}


ORDER_CREATE_KEYS = {
    "id",
    "customer_user",
    "business_user",
    "title",
    "revisions",
    "delivery_time_in_days",
    "price",
    "features",
    "offer_type",
    "status",
    "created_at",
}


OFFER_PAYLOAD = {
    "title": "Grafikdesign-Paket",
    "image": None,
    "description": "Ein umfassendes Grafikdesign-Paket für Unternehmen.",
    "details": [
                {
                    "title": "Basic Design",
                    "revisions": 2,
                    "delivery_time_in_days": 5,
                    "price": 100,
                    "features": ["Logo Design", "Visitenkarte"],
                    "offer_type": "basic",
                },
        {
                    "title": "Standard Design",
                    "revisions": 5,
                    "delivery_time_in_days": 7,
                    "price": 200,
                    "features": ["Logo Design", "Visitenkarte", "Briefpapier"],
                    "offer_type": "standard",
                },
        {
                    "title": "Premium Design",
                    "revisions": 10,
                    "delivery_time_in_days": 10,
                    "price": 500,
                    "features": ["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
                    "offer_type": "premium",
                },
    ],
}


def _build_offer_payload():
    return deepcopy(OFFER_PAYLOAD)


def _assert_order_keys(testcase, data, expected_keys):
    for key in expected_keys:
        testcase.assertIn(key, data)


def _create_user(user_model, username, email, password, **kwargs):
    return user_model.objects.create_user(username=username, email=email, password=password, **kwargs)


class OrdersListApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = _create_user(
            self.user_model, "orders_list_user", "orders_list_user@example.com", "testpass123")
        self.url = "/api/orders/"

    def test_get_orders_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_orders_success_structure(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)

        if data:
            _assert_order_keys(self, data[0], ORDER_KEYS)


class OrdersCreateApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.customer_user = _create_user(
            self.user_model, "customer_user", "customer_user@example.com", "testpass123")
        self.business_user = _create_user(
            self.user_model, "business_user", "business_user@example.com", "testpass123")
        self.url = "/api/orders/"
        self.offers_url = "/api/offers/"
        self.offer_payload = _build_offer_payload()

    def _create_offer_and_get_detail_id(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(
            self.offers_url, self.offer_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        details = response.json().get("details", [])
        self.assertTrue(details)
        return details[0].get("id")

    def test_create_order_requires_authentication(self):
        response = self.client.post(
            self.url, {"offer_detail_id": 1}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_forbidden_for_non_customer(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(
            self.url, {"offer_detail_id": 1}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_missing_offer_detail_id(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_offer_detail_id_invalid_type(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(
            self.url, {"offer_detail_id": "not-an-integer"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_offer_detail_not_found(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(
            self.url, {"offer_detail_id": 999999}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_order_success(self):
        detail_id = self._create_offer_and_get_detail_id()
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(
            self.url, {"offer_detail_id": detail_id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        _assert_order_keys(self, data, ORDER_CREATE_KEYS)


class OrdersUpdateApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.customer_user = _create_user(
            self.user_model, "customer_status", "customer_status@example.com", "testpass123")
        self.business_user = _create_user(
            self.user_model, "business_status", "business_status@example.com", "testpass123")
        self.other_business_user = _create_user(
            self.user_model, "other_business", "other_business@example.com", "testpass123")
        self.orders_url = "/api/orders/"
        self.offers_url = "/api/offers/"
        self.offer_payload = _build_offer_payload()

    def _create_offer_and_get_detail_id(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(
            self.offers_url, self.offer_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        details = response.json().get("details", [])
        self.assertTrue(details)
        return details[0].get("id")

    def _create_order(self):
        detail_id = self._create_offer_and_get_detail_id()
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(
            self.orders_url, {"offer_detail_id": detail_id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json().get("id")

    def test_patch_order_requires_authentication(self):
        response = self.client.patch(
            f"{self.orders_url}1/", {"status": "completed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_order_not_found(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.patch(
            f"{self.orders_url}999999/", {"status": "completed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_order_forbidden_for_non_business(self):
        order_id = self._create_order()
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.patch(
            f"{self.orders_url}{order_id}/", {"status": "completed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_order_forbidden_for_other_business(self):
        order_id = self._create_order()
        self.client.force_authenticate(user=self.other_business_user)
        response = self.client.patch(
            f"{self.orders_url}{order_id}/", {"status": "completed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_order_invalid_status_returns_400(self):
        order_id = self._create_order()
        self.client.force_authenticate(user=self.business_user)
        response = self.client.patch(
            f"{self.orders_url}{order_id}/", {"status": "not_valid"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_order_success(self):
        order_id = self._create_order()
        self.client.force_authenticate(user=self.business_user)
        response = self.client.patch(
            f"{self.orders_url}{order_id}/", {"status": "completed"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        _assert_order_keys(self, data, ORDER_KEYS)
        self.assertEqual(data["status"], "completed")


class OrdersDeleteApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.staff_user = _create_user(
            self.user_model,
            "staff_user",
            "staff_user@example.com",
            "testpass123",
            is_staff=True,
        )
        self.normal_user = _create_user(
            self.user_model, "normal_user", "normal_user@example.com", "testpass123")
        self.customer_user = _create_user(
            self.user_model, "customer_delete", "customer_delete@example.com", "testpass123")
        self.business_user = _create_user(
            self.user_model, "business_delete", "business_delete@example.com", "testpass123")
        self.orders_url = "/api/orders/"
        self.offers_url = "/api/offers/"
        self.offer_payload = _build_offer_payload()

    def _create_offer_and_get_detail_id(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(
            self.offers_url, self.offer_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        details = response.json().get("details", [])
        self.assertTrue(details)
        return details[0].get("id")

    def _create_order(self):
        detail_id = self._create_offer_and_get_detail_id()
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(
            self.orders_url, {"offer_detail_id": detail_id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json().get("id")

    def test_delete_order_requires_authentication(self):
        response = self.client.delete(f"{self.orders_url}1/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_order_forbidden_for_non_staff(self):
        order_id = self._create_order()
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.delete(f"{self.orders_url}{order_id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_order_not_found(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.delete(f"{self.orders_url}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_order_success_returns_204_no_content(self):
        order_id = self._create_order()
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.delete(f"{self.orders_url}{order_id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")


class OrdersCountApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.business_user = _create_user(
            self.user_model, "count_business", "count_business@example.com", "testpass123")
        self.url_base = "/api/order-count/"

    def test_get_order_count_requires_authentication(self):
        response = self.client.get(f"{self.url_base}{self.business_user.pk}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_order_count_not_found(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.get(f"{self.url_base}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_order_count_success_response(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.get(f"{self.url_base}{self.business_user.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("order_count", data)


class CompletedOrdersCountApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.business_user = _create_user(
            self.user_model,
            "completed_business",
            "completed_business@example.com",
            "testpass123",
        )
        self.url_base = "/api/completed-order-count/"

    def test_get_completed_order_count_requires_authentication(self):
        response = self.client.get(f"{self.url_base}{self.business_user.pk}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_completed_order_count_not_found(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.get(f"{self.url_base}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_completed_order_count_success_response(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.get(f"{self.url_base}{self.business_user.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("completed_order_count", data)
