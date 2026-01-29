from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class ProfileDetailApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.user = self.user_model.objects.create_user(
			username="max_mustermann",
			email="max@business.de",
			password="testpass123",
			first_name="Max",
			last_name="Mustermann",
		)
		self.other_user = self.user_model.objects.create_user(
			username="other_user",
			email="other@business.de",
			password="testpass123",
		)
		self.url = f"/api/profile/{self.user.pk}/"

	def test_get_profile_requires_authentication(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_profile_not_found(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.get("/api/profile/999999/")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_get_profile_success_fields_and_non_null_strings(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()

		expected_keys = {
			"user",
			"username",
			"first_name",
			"last_name",
			"file",
			"location",
			"tel",
			"description",
			"working_hours",
			"type",
			"email",
			"created_at",
		}
		for key in expected_keys:
			self.assertIn(key, data)

		for key in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
			self.assertIsNotNone(data[key])
			self.assertIsInstance(data[key], str)

	def test_patch_profile_updates_fields(self):
		self.client.force_authenticate(user=self.user)

		payload = {
			"first_name": "Maximilian",
			"last_name": "Mustermann",
			"location": "Berlin",
			"tel": "987654321",
			"description": "Updated business description",
			"working_hours": "10-18",
			"email": "new_email@business.de",
		}

		response = self.client.patch(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()
		for key, value in payload.items():
			self.assertEqual(data[key], value)
		for key in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
			self.assertIsNotNone(data[key])
			self.assertIsInstance(data[key], str)

	def test_patch_profile_requires_authentication(self):
		payload = {
			"first_name": "Max",
		}

		response = self.client.patch(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_patch_profile_forbidden_if_not_owner(self):
		self.client.force_authenticate(user=self.other_user)
		payload = {
			"first_name": "NotAllowed",
		}

		response = self.client.patch(self.url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_patch_profile_not_found(self):
		self.client.force_authenticate(user=self.user)
		payload = {
			"first_name": "Max",
		}

		response = self.client.patch("/api/profile/999999/", payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BusinessProfilesListApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.business_user = self.user_model.objects.create_user(
			username="max_business",
			email="max_business@example.com",
			password="testpass123",
			first_name="Max",
			last_name="Mustermann",
		)
		self.customer_user = self.user_model.objects.create_user(
			username="max_customer",
			email="max_customer@example.com",
			password="testpass123",
			first_name="Max",
			last_name="Mustermann",
		)
		self.url = "/api/profiles/business/"

	def test_get_business_profiles_requires_authentication(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_business_profiles_success_fields_and_non_null_strings(self):
		self.client.force_authenticate(user=self.business_user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()
		self.assertIsInstance(data, list)

		if data:
			first_item = data[0]
			expected_keys = {
				"user",
				"username",
				"first_name",
				"last_name",
				"file",
				"location",
				"tel",
				"description",
				"working_hours",
				"type",
			}
			for key in expected_keys:
				self.assertIn(key, first_item)

			for key in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
				self.assertIsNotNone(first_item[key])
				self.assertIsInstance(first_item[key], str)


class CustomerProfilesListApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.customer_user = self.user_model.objects.create_user(
			username="customer_jane",
			email="customer_jane@example.com",
			password="testpass123",
			first_name="Jane",
			last_name="Doe",
		)
		self.business_user = self.user_model.objects.create_user(
			username="biz_max",
			email="biz_max@example.com",
			password="testpass123",
			first_name="Max",
			last_name="Mustermann",
		)
		self.url = "/api/profiles/customer/"

	def test_get_customer_profiles_requires_authentication(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_customer_profiles_success_fields_and_non_null_strings(self):
		self.client.force_authenticate(user=self.customer_user)

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()
		self.assertIsInstance(data, list)

		if data:
			first_item = data[0]
			expected_keys = {
				"user",
				"username",
				"first_name",
				"last_name",
				"file",
				"type",
			}
			for key in expected_keys:
				self.assertIn(key, first_item)

			for key in ["first_name", "last_name"]:
				self.assertIsNotNone(first_item[key])
				self.assertIsInstance(first_item[key], str)


