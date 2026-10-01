from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)

PERFORMANCE_URL = reverse("performance-list")


class PerformanceApiTests(APITestCase):
    def setUp(self):
        hall = TheatreHall.objects.create(
            name="Small hall", rows=2, seats_in_row=2
        )
        play = Play.objects.create(title="Hamlet", description="A tragedy")
        play.actors.set(
            [
                Actor.objects.create(first_name="First", last_name="Actor"),
                Actor.objects.create(first_name="Second", last_name="Actor"),
            ]
        )
        play.genres.set(
            [
                Genre.objects.create(name="Drama"),
                Genre.objects.create(name="Tragedy"),
            ]
        )
        show_time = datetime(2026, 10, 1, 18, tzinfo=timezone.utc)
        self.performance = Performance.objects.create(
            play=play, theatre_hall=hall, show_time=show_time
        )
        self.other_performance = Performance.objects.create(
            play=play,
            theatre_hall=hall,
            show_time=show_time + timedelta(days=1),
        )

    def available_seats(self):
        response = self.client.get(PERFORMANCE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {
            item["id"]: item["tickets_available"]
            for item in response.data["results"]
        }

    def test_available_seats_are_counted_per_performance(self):
        self.assertEqual(
            self.available_seats(),
            {self.performance.pk: 4, self.other_performance.pk: 4},
        )
        user = get_user_model().objects.create_user(username="ticket_owner")
        reservation = Reservation.objects.create(user=user)
        for row in (1, 2):
            for seat in (1, 2):
                Ticket.objects.create(
                    row=row,
                    seat=seat,
                    performance=self.performance,
                    reservation=reservation,
                )
                expected_remaining = 4 - ((row - 1) * 2 + seat)
                self.assertEqual(
                    self.available_seats(),
                    {
                        self.performance.pk: expected_remaining,
                        self.other_performance.pk: 4,
                    },
                )

    def test_invalid_dates_return_400(self):
        for date in ("abc", "2026-02-30", "2026-13-01"):
            with self.subTest(date=date):
                response = self.client.get(PERFORMANCE_URL, {"date": date})
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST
                )

    def test_valid_date_still_filters_performances(self):
        response = self.client.get(
            PERFORMANCE_URL, {"date": "2026-10-01"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in response.data["results"]],
            [self.performance.pk],
        )
        self.assertEqual(
            response.data["results"][0]["tickets_available"], 4
        )
