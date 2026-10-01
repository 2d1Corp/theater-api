from django.db import IntegrityError, transaction
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name"]


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ["id", "name", "rows", "seats_in_row"]
        extra_kwargs = {
            "rows": {"min_value": 1},
            "seats_in_row": {"min_value": 1},
        }


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ["id", "title", "description", "actors", "genres"]


class PlayListSerializer(PlaySerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ["id", "play", "theatre_hall", "show_time"]


class PerformanceListSerializer(PerformanceSerializer):
    play = PlayListSerializer(read_only=True)
    theatre_hall = TheatreHallSerializer(read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta(PerformanceSerializer.Meta):
        fields = PerformanceSerializer.Meta.fields + ["tickets_available"]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "performance"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        ticket = Ticket(**attrs)

        try:
            ticket.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict)

        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = Reservation
        fields = ["id", "created_at", "tickets"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        tickets = attrs["tickets"]

        ticket_places = [
            (
                ticket["performance"].id,
                ticket["row"],
                ticket["seat"],
            )
            for ticket in tickets
        ]

        if len(ticket_places) != len(set(ticket_places)):
            raise serializers.ValidationError(
                {
                    "tickets": (
                        "Each seat may appear only once " "in a reservation."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")

        try:
            with transaction.atomic():
                reservation = Reservation.objects.create(**validated_data)

                for ticket_data in tickets_data:
                    Ticket.objects.create(
                        reservation=reservation,
                        **ticket_data,
                    )

        except IntegrityError as error:
            raise serializers.ValidationError(
                {"tickets": ("One or more seats are already reserved.")}
            ) from error

        return reservation
