from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase


CREATE_USER_URL = reverse("create")
ME_URL = reverse("manage")


class PublicUserApiTests(APITestCase):
    def test_create_user(self):
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        }

        response = self.client.post(
            CREATE_USER_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = get_user_model().objects.get(
            username=payload["username"]
        )

        self.assertTrue(
            user.check_password(payload["password"])
        )
        self.assertNotIn("password", response.data)

    def test_authentication_required_for_me(self):
        response = self.client.get(ME_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class PrivateUserApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_user_profile(self):
        response = self.client.get(ME_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data["username"],
            self.user.username,
        )
        self.assertEqual(
            response.data["email"],
            self.user.email,
        )
        self.assertNotIn("password", response.data)

    def test_update_user_password(self):
        payload = {
            "password": "newpassword123",
        }

        response = self.client.patch(
            ME_URL,
            payload,
            format="json",
        )

        self.user.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            self.user.check_password(payload["password"])
        )