from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from theatre.models import Actor, Genre, Performance, Play, TheatreHall
from theatre.permissions import IsAdminOrReadOnly
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PerformanceListSerializer, PerformanceSerializer, PlayListSerializer, PlaySerializer, TheatreHallSerializer
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [IsAdminOrReadOnly]


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = [IsAdminOrReadOnly]


def params_to_ints(query_string):
    try:
        return [int(value) for value in query_string.split(",")]
    except ValueError:
        raise ValidationError(
            "Query parameters must be integers separated by commas."
        )


class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("actors", "genres")
    serializer_class = PlaySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer

        return PlaySerializer

    def get_queryset(self):
        queryset = self.queryset
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genres:
            genre_ids = params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)

        if actors:
            actor_ids = params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)

        return queryset.distinct()

class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.select_related(
        "play",
        "theatre_hall",
    ).prefetch_related(
        "play__actors",
        "play__genres",
    )
    serializer_class = PerformanceSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        return PerformanceSerializer

    def get_queryset(self):
        queryset = self.queryset
        show_date = self.request.query_params.get("date")
        plays = self.request.query_params.get("plays")

        if show_date:
            parsed_date = parse_date(show_date)

            if parsed_date is None:
                raise ValidationError(
                    "Date must use YYYY-MM-DD format."
                )

            queryset = queryset.filter(
                show_time__date=parsed_date
            )

        if plays:
            play_ids = params_to_ints(plays)
            queryset = queryset.filter(
                play_id__in=play_ids
            )

        return queryset