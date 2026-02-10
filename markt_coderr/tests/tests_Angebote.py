from copy import deepcopy

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


def _assert_pagination_payload(testcase, data):
    for key in ["count", "next", "previous", "results"]:
        testcase.assertIn(key, data)
    testcase.assertIsInstance(data["results"], list)


def _assert_offer_list_item(testcase, item):
    expected_keys = {
        "id",
        "user",
        "title",
        "image",
        "description",
        "created_at",
        "updated_at",
        "details",
        "min_price",
        "min_delivery_time",
        "user_details",
    }
    for key in expected_keys:
        testcase.assertIn(key, item)


def _assert_offer_detail_response(testcase, data):
    expected_keys = {
        "id",
        "user",
        "title",
        "image",
        "description",
        "created_at",
        "updated_at",
        "details",
        "min_price",
        "min_delivery_time",
    }
    for key in expected_keys:
        testcase.assertIn(key, data)
    testcase.assertIsInstance(data["details"], list)


def _assert_offer_detail_link(testcase, detail):
    testcase.assertIn("id", detail)
    testcase.assertIn("url", detail)


def _assert_offer_create_response(testcase, data, payload):
    testcase.assertIn("id", data)
    testcase.assertEqual(data["title"], payload["title"])
    testcase.assertEqual(data["description"], payload["description"])
    testcase.assertIn("details", data)
    testcase.assertEqual(len(data["details"]), 3)
    for detail in data["details"]:
        testcase.assertIn("id", detail)


def _assert_offer_update_response(testcase, data, offer_id, payload):
    testcase.assertEqual(data["id"], offer_id)
    testcase.assertEqual(data["title"], payload["title"])
    testcase.assertIn("details", data)
    testcase.assertEqual(len(data["details"]), 3)
    basic_detail = next(
        (d for d in data["details"] if d.get("offer_type") == "basic"), None)
    testcase.assertIsNotNone(basic_detail)
    testcase.assertEqual(basic_detail["title"], payload["details"][0]["title"])


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


OFFER_UPDATE_PAYLOAD = {
    "title": "Updated Grafikdesign-Paket",
    "details": [
        {
            "title": "Basic Design Updated",
            "revisions": 3,
            "delivery_time_in_days": 6,
            "price": 120,
            "features": ["Logo Design", "Flyer"],
            "offer_type": "basic",
        },
    ],
}


def _build_offer_payload():
    return deepcopy(OFFER_PAYLOAD)


def _build_offer_update_payload():
    return deepcopy(OFFER_UPDATE_PAYLOAD)


def _create_user(user_model, username, email, password, **kwargs):
    return user_model.objects.create_user(username=username, email=email, password=password, **kwargs)


class OffersListApiTests(APITestCase):
    def setUp(self):
        self.url = "/api/offers/"

    def test_get_offers_list_success_with_pagination_structure(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        _assert_pagination_payload(self, data)
        if data["results"]:
            _assert_offer_list_item(self, data["results"][0])

    def test_get_offers_list_invalid_ordering_returns_400(self):
        response = self.client.get(self.url, {"ordering": "invalid_field"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OffersCreateApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.business_user = _create_user(
            self.user_model, "biz_user", "biz_user@example.com", "testpass123")
        self.customer_user = _create_user(
            self.user_model, "customer_user", "customer_user@example.com", "testpass123")
        self.url = "/api/offers/"
        self.payload = _build_offer_payload()

    def test_create_offer_requires_authentication(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_offer_forbidden_for_non_business(self):
        self.client.force_authenticate(user=self.customer_user)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_offer_requires_three_details(self):
        self.client.force_authenticate(user=self.business_user)
        payload = {**self.payload, "details": self.payload["details"][:2]}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_offer_success(self):
        self.client.force_authenticate(user=self.business_user)

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        _assert_offer_create_response(self, data, self.payload)


class OffersDetailApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.business_user = _create_user(
            self.user_model, "biz_detail_user", "biz_detail_user@example.com", "testpass123")
        self.other_user = _create_user(
            self.user_model, "other_offer_user", "other_offer_user@example.com", "testpass123")
        self.url_base = "/api/offers/"
        self.payload = _build_offer_payload()

    def test_get_offer_detail_requires_authentication(self):
        response = self.client.get(f"{self.url_base}1/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offer_detail_not_found(self):
        self.client.force_authenticate(user=self.business_user)

        response = self.client.get(f"{self.url_base}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_offer_detail_success(self):
        self.client.force_authenticate(user=self.business_user)

        create_response = self.client.post(
            self.url_base, self.payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        offer_id = create_response.json().get("id")

        response = self.client.get(f"{self.url_base}{offer_id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        _assert_offer_detail_response(self, data)
        if data["details"]:
            _assert_offer_detail_link(self, data["details"][0])


class OffersUpdateApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.owner_user = _create_user(
            self.user_model, "owner_user", "owner_user@example.com", "testpass123")
        self.other_user = _create_user(
            self.user_model, "not_owner_user", "not_owner_user@example.com", "testpass123")
        self.url_base = "/api/offers/"
        self.create_payload = _build_offer_payload()
        self.update_payload = _build_offer_update_payload()

    def _create_offer(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.post(
            self.url_base, self.create_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json().get("id")

    def test_patch_offer_requires_authentication(self):
        response = self.client.patch(
            f"{self.url_base}1/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_offer_not_found(self):
        self.client.force_authenticate(user=self.owner_user)

        response = self.client.patch(
            f"{self.url_base}999999/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_offer_forbidden_for_non_owner(self):
        offer_id = self._create_offer()
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            f"{self.url_base}{offer_id}/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_offer_success(self):
        offer_id = self._create_offer()
        self.client.force_authenticate(user=self.owner_user)

        response = self.client.patch(
            f"{self.url_base}{offer_id}/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        _assert_offer_update_response(
            self, data, offer_id, self.update_payload)


class OffersDeleteApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.owner_user = _create_user(
            self.user_model, "delete_owner", "delete_owner@example.com", "testpass123")
        self.other_user = _create_user(
            self.user_model, "delete_other", "delete_other@example.com", "testpass123")
        self.url_base = "/api/offers/"
        self.create_payload = _build_offer_payload()

    def _create_offer(self):
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.post(
            self.url_base, self.create_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json().get("id")

    def test_delete_offer_requires_authentication(self):
        response = self.client.delete(f"{self.url_base}1/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_offer_not_found(self):
        self.client.force_authenticate(user=self.owner_user)

        response = self.client.delete(f"{self.url_base}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_offer_forbidden_for_non_owner(self):
        offer_id = self._create_offer()
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(f"{self.url_base}{offer_id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_offer_success_returns_204_no_content(self):
        offer_id = self._create_offer()
        self.client.force_authenticate(user=self.owner_user)

        response = self.client.delete(f"{self.url_base}{offer_id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")


class OfferDetailsRetrieveApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.business_user = _create_user(
            self.user_model, "detail_owner", "detail_owner@example.com", "testpass123")
        self.offers_url = "/api/offers/"
        self.details_url_base = "/api/offerdetails/"
        self.create_payload = _build_offer_payload()

    def _create_offer_and_get_detail_id(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(
            self.offers_url, self.create_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        details = response.json().get("details", [])
        self.assertTrue(details)
        return details[0].get("id")

    def test_get_offerdetail_requires_authentication(self):
        response = self.client.get(f"{self.details_url_base}1/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_offerdetail_not_found(self):
        self.client.force_authenticate(user=self.business_user)

        response = self.client.get(f"{self.details_url_base}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_offerdetail_success(self):
        detail_id = self._create_offer_and_get_detail_id()
        self.client.force_authenticate(user=self.business_user)

        response = self.client.get(f"{self.details_url_base}{detail_id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        expected_keys = {
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        }
        for key in expected_keys:
            self.assertIn(key, data)
