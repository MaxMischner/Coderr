from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class OffersListApiTests(APITestCase):
	def setUp(self):
		self.url = "/api/offers/"

	def test_get_offers_list_success_with_pagination_structure(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()

		self.assertIn("count", data)
		self.assertIn("next", data)
		self.assertIn("previous", data)
		self.assertIn("results", data)
		self.assertIsInstance(data["results"], list)

		if data["results"]:
			first_item = data["results"][0]
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
				self.assertIn(key, first_item)

	def test_get_offers_list_invalid_ordering_returns_400(self):
		response = self.client.get(self.url, {"ordering": "invalid_field"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OffersCreateApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.business_user = self.user_model.objects.create_user(
			username="biz_user",
			email="biz_user@example.com",
			password="testpass123",
		)
		self.customer_user = self.user_model.objects.create_user(
			username="customer_user",
			email="customer_user@example.com",
			password="testpass123",
		)
		self.url = "/api/offers/"
		self.payload = {
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

		self.assertIn("id", data)
		self.assertEqual(data["title"], self.payload["title"])
		self.assertEqual(data["description"], self.payload["description"])
		self.assertIn("details", data)
		self.assertEqual(len(data["details"]), 3)
		for detail in data["details"]:
			self.assertIn("id", detail)


class OffersDetailApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.business_user = self.user_model.objects.create_user(
			username="biz_detail_user",
			email="biz_detail_user@example.com",
			password="testpass123",
		)
		self.other_user = self.user_model.objects.create_user(
			username="other_offer_user",
			email="other_offer_user@example.com",
			password="testpass123",
		)
		self.url_base = "/api/offers/"
		self.payload = {
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

	def test_get_offer_detail_requires_authentication(self):
		response = self.client.get(f"{self.url_base}1/")

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_get_offer_detail_not_found(self):
		self.client.force_authenticate(user=self.business_user)

		response = self.client.get(f"{self.url_base}999999/")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_get_offer_detail_success(self):
		self.client.force_authenticate(user=self.business_user)

		create_response = self.client.post(self.url_base, self.payload, format="json")
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		offer_id = create_response.json().get("id")

		response = self.client.get(f"{self.url_base}{offer_id}/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()

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
			self.assertIn(key, data)

		self.assertIsInstance(data["details"], list)
		if data["details"]:
			self.assertIn("id", data["details"][0])
			self.assertIn("url", data["details"][0])


class OffersUpdateApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.owner_user = self.user_model.objects.create_user(
			username="owner_user",
			email="owner_user@example.com",
			password="testpass123",
		)
		self.other_user = self.user_model.objects.create_user(
			username="not_owner_user",
			email="not_owner_user@example.com",
			password="testpass123",
		)
		self.url_base = "/api/offers/"
		self.create_payload = {
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
					"delivery_time_in_days": 10,
					"price": 120,
					"features": ["Logo Design", "Visitenkarte", "Briefpapier"],
					"offer_type": "standard",
				},
				{
					"title": "Premium Design",
					"revisions": 10,
					"delivery_time_in_days": 10,
					"price": 150,
					"features": ["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
					"offer_type": "premium",
				},
			],
		}
		self.update_payload = {
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

	def _create_offer(self):
		self.client.force_authenticate(user=self.owner_user)
		response = self.client.post(self.url_base, self.create_payload, format="json")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		return response.json().get("id")

	def test_patch_offer_requires_authentication(self):
		response = self.client.patch(f"{self.url_base}1/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_patch_offer_not_found(self):
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.patch(f"{self.url_base}999999/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_patch_offer_forbidden_for_non_owner(self):
		offer_id = self._create_offer()
		self.client.force_authenticate(user=self.other_user)

		response = self.client.patch(f"{self.url_base}{offer_id}/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_patch_offer_success(self):
		offer_id = self._create_offer()
		self.client.force_authenticate(user=self.owner_user)

		response = self.client.patch(f"{self.url_base}{offer_id}/", self.update_payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()

		self.assertEqual(data["id"], offer_id)
		self.assertEqual(data["title"], self.update_payload["title"])
		self.assertIn("details", data)
		self.assertEqual(len(data["details"]), 3)
		basic_detail = next((d for d in data["details"] if d.get("offer_type") == "basic"), None)
		self.assertIsNotNone(basic_detail)
		self.assertEqual(basic_detail["title"], "Basic Design Updated")


class OffersDeleteApiTests(APITestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.owner_user = self.user_model.objects.create_user(
			username="delete_owner",
			email="delete_owner@example.com",
			password="testpass123",
		)
		self.other_user = self.user_model.objects.create_user(
			username="delete_other",
			email="delete_other@example.com",
			password="testpass123",
		)
		self.url_base = "/api/offers/"
		self.create_payload = {
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
					"delivery_time_in_days": 10,
					"price": 120,
					"features": ["Logo Design", "Visitenkarte", "Briefpapier"],
					"offer_type": "standard",
				},
				{
					"title": "Premium Design",
					"revisions": 10,
					"delivery_time_in_days": 10,
					"price": 150,
					"features": ["Logo Design", "Visitenkarte", "Briefpapier", "Flyer"],
					"offer_type": "premium",
				},
			],
		}

	def _create_offer(self):
		self.client.force_authenticate(user=self.owner_user)
		response = self.client.post(self.url_base, self.create_payload, format="json")
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
		self.business_user = self.user_model.objects.create_user(
			username="detail_owner",
			email="detail_owner@example.com",
			password="testpass123",
		)
		self.offers_url = "/api/offers/"
		self.details_url_base = "/api/offerdetails/"
		self.create_payload = {
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

	def _create_offer_and_get_detail_id(self):
		self.client.force_authenticate(user=self.business_user)
		response = self.client.post(self.offers_url, self.create_payload, format="json")
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
