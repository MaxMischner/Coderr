from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class ReviewsListApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.user = self.user_model.objects.create_user(
			username="reviews_list_user",
			email="reviews_list_user@example.com",
			password="testpass123",
		)
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
			first_item = data[0]
			expected_keys = {
				"id",
				"business_user",
				"reviewer",
				"rating",
				"description",
				"created_at",
				"updated_at",
			}
			for key in expected_keys:
				self.assertIn(key, first_item)

	def test_get_reviews_invalid_ordering_returns_400(self):
		self.client.force_authenticate(user=self.user)
		response = self.client.get(self.url, {"ordering": "invalid"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewsCreateApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.customer_user = self.user_model.objects.create_user(
			username="review_customer",
			email="review_customer@example.com",
			password="testpass123",
		)
		self.business_user = self.user_model.objects.create_user(
			username="review_business",
			email="review_business@example.com",
			password="testpass123",
		)
		self.other_customer = self.user_model.objects.create_user(
			username="review_customer2",
			email="review_customer2@example.com",
			password="testpass123",
		)
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
		expected_keys = {
			"id",
			"business_user",
			"reviewer",
			"rating",
			"description",
			"created_at",
			"updated_at",
		}
		for key in expected_keys:
			self.assertIn(key, data)
		self.assertEqual(data["business_user"], self.business_user.pk)
		self.assertEqual(data["rating"], 4)

	def test_create_review_duplicate_for_business_forbidden(self):
		self.client.force_authenticate(user=self.customer_user)
		first = self.client.post(self.url, self.payload, format="json")
		self.assertEqual(first.status_code, status.HTTP_201_CREATED)

		second = self.client.post(self.url, self.payload, format="json")
		self.assertIn(second.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])


class ReviewsUpdateApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.reviewer = self.user_model.objects.create_user(
			username="review_owner",
			email="review_owner@example.com",
			password="testpass123",
		)
		self.other_user = self.user_model.objects.create_user(
			username="review_other",
			email="review_other@example.com",
			password="testpass123",
		)
		self.business_user = self.user_model.objects.create_user(
			username="review_target",
			email="review_target@example.com",
			password="testpass123",
		)
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
		response = self.client.post(self.url_base, self.create_payload, format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		return response.json().get("id")

	def test_patch_review_requires_authentication(self):
		response = self.client.patch(f"{self.url_base}1/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_patch_review_not_found(self):
		self.client.force_authenticate(user=self.reviewer)
		response = self.client.patch(f"{self.url_base}999999/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_patch_review_forbidden_for_non_owner(self):
		review_id = self._create_review()
		self.client.force_authenticate(user=self.other_user)
		response = self.client.patch(f"{self.url_base}{review_id}/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_patch_review_invalid_data_returns_400(self):
		review_id = self._create_review()
		self.client.force_authenticate(user=self.reviewer)
		response = self.client.patch(f"{self.url_base}{review_id}/", {"rating": 999}, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_patch_review_success(self):
		review_id = self._create_review()
		self.client.force_authenticate(user=self.reviewer)
		response = self.client.patch(f"{self.url_base}{review_id}/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()
		expected_keys = {
			"id",
			"business_user",
			"reviewer",
			"rating",
			"description",
			"created_at",
			"updated_at",
		}
		for key in expected_keys:
			self.assertIn(key, data)
		self.assertEqual(data["rating"], 5)
		self.assertEqual(data["description"], "Noch besser als erwartet!")


class ReviewsDeleteApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.reviewer = self.user_model.objects.create_user(
			username="delete_reviewer",
			email="delete_reviewer@example.com",
			password="testpass123",
		)
		self.other_user = self.user_model.objects.create_user(
			username="delete_other",
			email="delete_other@example.com",
			password="testpass123",
		)
		self.business_user = self.user_model.objects.create_user(
			username="delete_business",
			email="delete_business@example.com",
			password="testpass123",
		)
		self.url_base = "/api/reviews/"
		self.create_payload = {
			"business_user": self.business_user.pk,
			"rating": 4,
			"description": "Alles war toll!",
		}

	def _create_review(self):
		self.client.force_authenticate(user=self.reviewer)
		response = self.client.post(self.url_base, self.create_payload, format="json")
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
