from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


REVIEW_KEYS = {
    "id",
    "business_user",
    "reviewer",
    "rating",
    "description",
    "created_at",
    "updated_at",
}


def _assert_review_keys(testcase, data):
    for key in REVIEW_KEYS:
        testcase.assertIn(key, data)


def _create_user(user_model, username, email, password, **kwargs):
    return user_model.objects.create_user(username=username, email=email, password=password, **kwargs)


class ReviewsListApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = _create_user(
            self.user_model, "reviews_list_user", "reviews_list_user@example.com", "testpass123")
        self.url = "/api/reviews/"

    def test_get_reviews_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_reviews_success_structure(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)

        if data:
            _assert_review_keys(self, data[0])

    def test_get_reviews_invalid_ordering_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {"ordering": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewsCreateApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.customer_user = _create_user(
            self.user_model, "review_customer", "review_customer@example.com", "testpass123")
        self.business_user = _create_user(
            self.user_model, "review_business", "review_business@example.com", "testpass123")
        self.other_customer = _create_user(
            self.user_model, "review_customer2", "review_customer2@example.com", "testpass123")
        self.url = "/api/reviews/"
        self.payload = {
            "business_user": self.business_user.pk,
            "rating": 4,
            "description": "Alles war toll!",
        }

    def test_create_review_requires_authentication(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_review_forbidden_for_non_customer(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_review_success(self):
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        _assert_review_keys(self, data)
        self.assertEqual(data["business_user"], self.business_user.pk)
        self.assertEqual(data["rating"], 4)

    def test_create_review_duplicate_for_business_forbidden(self):
        self.client.force_authenticate(user=self.customer_user)
        first = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(self.url, self.payload, format="json")
        self.assertIn(second.status_code, [
                      status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])


class ReviewsUpdateApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.reviewer = _create_user(
            self.user_model, "review_owner", "review_owner@example.com", "testpass123")
        self.other_user = _create_user(
            self.user_model, "review_other", "review_other@example.com", "testpass123")
        self.business_user = _create_user(
            self.user_model, "review_target", "review_target@example.com", "testpass123")
        self.url_base = "/api/reviews/"
        self.create_payload = {
            "business_user": self.business_user.pk,
            "rating": 4,
            "description": "Alles war toll!",
        }
        self.update_payload = {
            "rating": 5,
            "description": "Noch besser als erwartet!",
        }

    def _create_review(self):
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.post(
            self.url_base, self.create_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json().get("id")

    def test_patch_review_requires_authentication(self):
        response = self.client.patch(
            f"{self.url_base}1/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_review_not_found(self):
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.patch(
            f"{self.url_base}999999/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_review_forbidden_for_non_owner(self):
        review_id = self._create_review()
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            f"{self.url_base}{review_id}/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_review_invalid_data_returns_400(self):
        review_id = self._create_review()
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.patch(
            f"{self.url_base}{review_id}/", {"rating": 999}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_review_success(self):
        review_id = self._create_review()
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.patch(
            f"{self.url_base}{review_id}/", self.update_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        _assert_review_keys(self, data)
        self.assertEqual(data["rating"], 5)
        self.assertEqual(data["description"], "Noch besser als erwartet!")


class ReviewsDeleteApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.reviewer = _create_user(
            self.user_model, "delete_reviewer", "delete_reviewer@example.com", "testpass123")
        self.other_user = _create_user(
            self.user_model, "delete_other", "delete_other@example.com", "testpass123")
        self.business_user = _create_user(
            self.user_model, "delete_business", "delete_business@example.com", "testpass123")
        self.url_base = "/api/reviews/"
        self.create_payload = {
            "business_user": self.business_user.pk,
            "rating": 4,
            "description": "Alles war toll!",
        }

    def _create_review(self):
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.post(
            self.url_base, self.create_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json().get("id")

    def test_delete_review_requires_authentication(self):
        response = self.client.delete(f"{self.url_base}1/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_review_not_found(self):
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.delete(f"{self.url_base}999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_review_forbidden_for_non_owner(self):
        review_id = self._create_review()
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f"{self.url_base}{review_id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_review_success_returns_204_no_content(self):
        review_id = self._create_review()
        self.client.force_authenticate(user=self.reviewer)
        response = self.client.delete(f"{self.url_base}{review_id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
