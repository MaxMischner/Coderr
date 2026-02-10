from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


PROFILE_DETAIL_KEYS = {
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


BUSINESS_PROFILE_KEYS = {
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


CUSTOMER_PROFILE_KEYS = {
    "user",
    "username",
    "first_name",
    "last_name",
    "file",
    "type",
}


def _assert_keys(testcase, data, expected_keys):
    for key in expected_keys:
        testcase.assertIn(key, data)


def _assert_non_null_strings(testcase, data, keys):
    for key in keys:
        testcase.assertIsNotNone(data[key])
        testcase.assertIsInstance(data[key], str)


def _create_user(user_model, username, email, password, **kwargs):
    return user_model.objects.create_user(username=username, email=email, password=password, **kwargs)


class ProfileDetailApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = _create_user(
            self.user_model,
            "max_mustermann",
            "max@business.de",
            "testpass123",
            first_name="Max",
            last_name="Mustermann",
        )
        self.other_user = _create_user(
            self.user_model, "other_user", "other@business.de", "testpass123")
        self.business_user = _create_user(
            self.user_model,
            "business_max",
            "new_email@business.de",
            "testpass123",
            first_name="Max",
            last_name="Mustermann",
        )
        self.url = f"/api/profile/{self.user.pk}/"
        self.business_url = f"/api/profile/{self.business_user.pk}/"

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
        _assert_keys(self, data, PROFILE_DETAIL_KEYS)
        _assert_non_null_strings(
            self,
            data,
            ["first_name", "last_name", "location",
                "tel", "description", "working_hours"],
        )

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
        _assert_non_null_strings(
            self,
            data,
            ["first_name", "last_name", "location",
                "tel", "description", "working_hours"],
        )

    def test_patch_business_profile_updates_fields_and_non_null_strings(self):
        self.client.force_authenticate(user=self.business_user)

        payload = {
            "first_name": "Max",
            "last_name": "Mustermann",
            "location": "Berlin",
            "tel": "987654321",
            "description": "Updated business description",
            "working_hours": "10-18",
            "email": "new_email@business.de",
        }

        response = self.client.patch(self.business_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        for key, value in payload.items():
            self.assertEqual(data[key], value)
        self.assertEqual(data["type"], "business")
        _assert_non_null_strings(
            self,
            data,
            ["first_name", "last_name", "location",
                "tel", "description", "working_hours"],
        )

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

        response = self.client.patch(
            "/api/profile/999999/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BusinessProfilesListApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.business_user = _create_user(
            self.user_model,
            "max_business",
            "max_business@example.com",
            "testpass123",
            first_name="Max",
            last_name="Mustermann",
        )
        self.customer_user = _create_user(
            self.user_model,
            "max_customer",
            "max_customer@example.com",
            "testpass123",
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
            _assert_keys(self, first_item, BUSINESS_PROFILE_KEYS)
            _assert_non_null_strings(
                self,
                first_item,
                ["first_name", "last_name", "location",
                    "tel", "description", "working_hours"],
            )


class CustomerProfilesListApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.customer_user = _create_user(
            self.user_model,
            "customer_jane",
            "customer_jane@example.com",
            "testpass123",
            first_name="Jane",
            last_name="Doe",
        )
        self.business_user = _create_user(
            self.user_model,
            "biz_max",
            "biz_max@example.com",
            "testpass123",
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
            _assert_keys(self, first_item, CUSTOMER_PROFILE_KEYS)
            _assert_non_null_strings(
                self, first_item, ["first_name", "last_name"])
