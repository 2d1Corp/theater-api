from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Genre(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name + " " + self.last_name


class TheatreHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(rows__gte=1), name="rows_gte_1"
            ),
            models.CheckConstraint(
                condition=Q(seats_in_row__gte=1), name="seats_in_row_gte_1"
            ),
        ]

    def __str__(self):
        return self.name


class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    actors = models.ManyToManyField(Actor, related_name="plays", blank=True)
    genres = models.ManyToManyField(Genre, related_name="plays", blank=True)

    def __str__(self):
        return self.title


class Performance(models.Model):
    play = models.ForeignKey(
        Play, related_name="performances", on_delete=models.PROTECT
    )
    theatre_hall = models.ForeignKey(
        TheatreHall, related_name="performances", on_delete=models.PROTECT
    )
    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.play.title} - {self.show_time:%Y-%m-%d %H:%M}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reservations",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"Reservation #{self.pk}"


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    performance = models.ForeignKey(
        Performance, related_name="tickets", on_delete=models.PROTECT
    )
    reservation = models.ForeignKey(
        Reservation, related_name="tickets", on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["row", "seat", "performance"],
                name="unique_ticket_seat_per_performance",
            ),
        ]

    def __str__(self):
        return f"{self.performance}, row {self.row}, seat {self.seat}"

    def clean(self):
        super().clean()

        if not self.performance_id:
            return

        hall = self.performance.theatre_hall

        if self.row is not None and not 1 <= self.row <= hall.rows:
            raise ValidationError({"row": "Row is outside the theatre hall."})
        if self.seat is not None and not 1 <= self.seat <= hall.seats_in_row:
            raise ValidationError({"seat": "Seat is outside the hall."})
