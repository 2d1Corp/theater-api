from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from theatre.models import Performance, Play, Reservation, TheatreHall, Ticket


class TicketTests(TestCase):
    def setUp(self):
        hall = TheatreHall.objects.create(
            name="Small Hall",
            rows=10,
            seats_in_row=20,
        )
        play = Play.objects.create(
            title="Hamlet",
            description="Test play",
        )
        self.performance = Performance.objects.create(
            play=play,
            theatre_hall=hall,
            show_time=timezone.now(),
        )
        user = get_user_model().objects.create_user(username="test_user")
        self.reservation = Reservation.objects.create(user=user)

    def test_row_outside_hall_is_rejected(self):
        ticket = Ticket(
            row=11,
            seat=1,
            performance=self.performance,
        )

        with self.assertRaises(ValidationError):
            ticket.clean()

    def test_seat_outside_hall_is_rejected(self):
        ticket = Ticket(
            row=1,
            seat=21,
            performance=self.performance,
        )

        with self.assertRaises(ValidationError):
            ticket.clean()

    def test_ticket_at_hall_boundary_is_valid(self):
        ticket = Ticket(
            row=10,
            seat=20,
            performance=self.performance,
        )

        ticket.clean()

    def test_zero_row_is_rejected(self):
        ticket = Ticket(
            row=0,
            seat=20,
            performance=self.performance,
        )

        with self.assertRaises(ValidationError):
            ticket.clean()

    def test_zero_seat_is_rejected(self):
        ticket = Ticket(
            row=10,
            seat=0,
            performance=self.performance,
        )

        with self.assertRaises(ValidationError):
            ticket.clean()

    def test_duplicate_seat_for_same_performance_is_rejected(self):
        Ticket.objects.create(
            row=10,
            seat=20,
            performance=self.performance,
            reservation=self.reservation,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ticket.objects.create(
                    row=10,
                    seat=20,
                    performance=self.performance,
                    reservation=self.reservation,
                )

    def test_same_seat_for_different_performance_is_allowed(self):
        other_performance = Performance.objects.create(
            play=self.performance.play,
            theatre_hall=self.performance.theatre_hall,
            show_time=self.performance.show_time + timedelta(days=1),
        )
        Ticket.objects.create(
            row=10,
            seat=20,
            performance=self.performance,
            reservation=self.reservation,
        )
        Ticket.objects.create(
            row=10,
            seat=20,
            performance=other_performance,
            reservation=self.reservation,
        )

        self.assertEqual(Ticket.objects.count(), 2)


class TheatreHallTests(TestCase):
    def test_zero_rows_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TheatreHall.objects.create(
                    name="Small Hall",
                    rows=0,
                    seats_in_row=20,
                )

    def test_zero_seats_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TheatreHall.objects.create(
                    name="Small Hall",
                    rows=10,
                    seats_in_row=0,
                )
