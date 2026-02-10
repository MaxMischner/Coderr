from rest_framework import status
from rest_framework.test import APITestCase


class BaseInfoApiTests(APITestCase):
    def setUp(self):
        self.url = "/api/base-info/"

    def test_get_base_info_success(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        for key in ["review_count", "average_rating", "business_profile_count", "offer_count"]:
            self.assertIn(key, data)
