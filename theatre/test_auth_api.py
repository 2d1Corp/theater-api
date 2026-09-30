from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from theatre.models import Genre


TOKEN_URL = reverse("token_obtain_pair")
TOKEN_REFRESH_URL = reverse("token_refresh")
GENRE_URL = reverse("genre-list")


class JwtApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="staff",
            password="testpass",
            is_staff=True,
        )

    def test_user_can_obtain_and_use_access_token(self):
        token_response = self.client.post(
            TOKEN_URL,
            {
                "username": "staff",
                "password": "testpass",
            },
            format="json",
        )

        self.assertEqual(
            token_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", token_response.data)
        self.assertIn("refresh", token_response.data)

        access_token = token_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        genre_response = self.client.post(
            GENRE_URL,
            {"name": "Drama"},
            format="json",
        )

        self.assertEqual(
            genre_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            Genre.objects.filter(name="Drama").exists()
        )

    def test_refresh_token_returns_new_access_token(self):
        token_response = self.client.post(
            TOKEN_URL,
            {
                "username": "staff",
                "password": "testpass",
            },
            format="json",
        )

        refresh_token = token_response.data["refresh"]

        response = self.client.post(
            TOKEN_REFRESH_URL,
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)