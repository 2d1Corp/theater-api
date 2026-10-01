from unittest.mock import patch

from django.db import IntegrityError
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from theatre.models import (
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)

RESERVATION_URL = reverse("reservation-list")


class ReservationApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.hall = TheatreHall.objects.create(
            name="Main Hall",
            rows=10,
            seats_in_row=20,
        )

        self.play = Play.objects.create(
            title="Hamlet",
            description="Test play",
        )

        self.performance = Performance.objects.create(
            play=self.play,
            theatre_hall=self.hall,
            show_time=timezone.now() + timedelta(days=1),
        )

    def test_authentication_required(self):
        response = self.client.get(RESERVATION_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_create_reservation_with_tickets(self):
        self.client.force_authenticate(self.user)

        payload = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 5,
                    "performance": self.performance.id,
                },
                {
                    "row": 2,
                    "seat": 6,
                    "performance": self.performance.id,
                },
            ]
        }

        response = self.client.post(
            RESERVATION_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            Reservation.objects.count(),
            1,
        )
        self.assertEqual(
            Ticket.objects.count(),
            2,
        )

        reservation = Reservation.objects.get()

        self.assertEqual(
            reservation.user,
            self.user,
        )

    def test_user_sees_only_own_reservations(self):
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        own_reservation = Reservation.objects.create(
            user=self.user,
        )
        Reservation.objects.create(
            user=other_user,
        )

        self.client.force_authenticate(self.user)

        response = self.client.get(RESERVATION_URL)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["count"],
            1,
        )
        self.assertEqual(
            response.data["results"][0]["id"],
            own_reservation.id,
        )

    def test_cannot_create_ticket_with_invalid_row(self):
        self.client.force_authenticate(self.user)

        payload = {
            "tickets": [
                {
                    "row": 11,
                    "seat": 5,
                    "performance": self.performance.id,
                }
            ]
        }

        response = self.client.post(
            RESERVATION_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            Reservation.objects.count(),
            0,
        )
        self.assertEqual(
            Ticket.objects.count(),
            0,
        )

    def test_cannot_create_duplicate_tickets_in_one_request(self):
        self.client.force_authenticate(self.user)

        payload = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 5,
                    "performance": self.performance.id,
                },
                {
                    "row": 2,
                    "seat": 5,
                    "performance": self.performance.id,
                },
            ]
        }

        response = self.client.post(
            RESERVATION_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            Reservation.objects.count(),
            0,
        )
        self.assertEqual(
            Ticket.objects.count(),
            0,
        )

    def test_cannot_book_already_reserved_seat(self):
        existing_reservation = Reservation.objects.create(
            user=self.user,
        )
        Ticket.objects.create(
            reservation=existing_reservation,
            performance=self.performance,
            row=2,
            seat=5,
        )

        self.client.force_authenticate(self.user)

        payload = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 5,
                    "performance": self.performance.id,
                }
            ]
        }

        response = self.client.post(
            RESERVATION_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            Reservation.objects.count(),
            1,
        )
        self.assertEqual(
            Ticket.objects.count(),
            1,
        )

    @patch("theatre.serializers.Ticket.objects.create")
    def test_database_conflict_returns_400_and_rolls_back(
        self,
        mocked_create,
    ):
        mocked_create.side_effect = IntegrityError

        self.client.force_authenticate(self.user)

        payload = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 5,
                    "performance": self.performance.id,
                }
            ]
        }

        response = self.client.post(
            RESERVATION_URL,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            Reservation.objects.count(),
            0,
        )
        self.assertEqual(
            Ticket.objects.count(),
            0,
        )
