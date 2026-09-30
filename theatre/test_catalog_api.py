from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from theatre.models import Genre, TheatreHall

GENRE_URL = reverse("genre-list")
HALL_URL = reverse("theatrehall-list")


class GenreApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user",
            password="testpass",
        )
        self.staff_user = get_user_model().objects.create_user(
            username="staff",
            password="testpass",
            is_staff=True,
        )

    def test_genre_list_is_public(self):
        response = self.client.get(GENRE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_genre(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            GENRE_URL,
            {"name": "Drama"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertFalse(
            Genre.objects.filter(name="Drama").exists()
        )

    def test_staff_user_can_create_genre(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            GENRE_URL,
            {"name": "Drama"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            Genre.objects.filter(name="Drama").exists()
        )


class TheatreHallApiTests(APITestCase):
    def setUp(self):
        self.staff_user = get_user_model().objects.create_user(
            username="hall_staff",
            password="testpass",
            is_staff=True,
        )

    def test_zero_rows_is_rejected(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            HALL_URL,
            {
                "name": "Invalid Hall",
                "rows": 0,
                "seats_in_row": 20,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(
            TheatreHall.objects.filter(name="Invalid Hall").exists()
        )