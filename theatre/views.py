from django.db.models import Count, F
from django.utils.dateparse import parse_date
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
)
from theatre.permissions import IsAdminOrReadOnly
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PerformanceListSerializer,
    PerformanceSerializer,
    PlayListSerializer,
    PlaySerializer,
    ReservationSerializer,
    TheatreHallSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.order_by("id")
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.order_by("id")
    serializer_class = ActorSerializer
    permission_classes = [IsAdminOrReadOnly]


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.order_by("id")
    serializer_class = TheatreHallSerializer
    permission_classes = [IsAdminOrReadOnly]


def params_to_ints(query_string):
    try:
        return [int(value) for value in query_string.split(",")]
    except ValueError:
        raise ValidationError(
            "Query parameters must be integers separated by commas."
        )


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="title",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Search plays by part of the title.",
            ),
            OpenApiParameter(
                name="genres",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filter by genre IDs separated by commas, e.g. 1,2."
                ),
            ),
            OpenApiParameter(
                name="actors",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filter by actor IDs separated by commas, e.g. 1,2."
                ),
            ),
        ],
    ),
)
class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("actors", "genres").order_by("id")
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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filter by show date in YYYY-MM-DD format."
                ),
            ),
            OpenApiParameter(
                name="plays",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filter by play IDs separated by commas, e.g. 1,2."
                ),
            ),
        ],
    ),
)
class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Performance.objects.select_related(
            "play",
            "theatre_hall",
        )
        .prefetch_related(
            "play__actors",
            "play__genres",
        )
        .annotate(
            tickets_available=(
                F("theatre_hall__rows")
                * F("theatre_hall__seats_in_row")
                - Count("tickets")
            )
        )
        .order_by("id")
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
            try:
                parsed_date = parse_date(show_date)
            except ValueError:
                parsed_date = None

            if parsed_date is None:
                raise ValidationError("Date must use YYYY-MM-DD format.")

            queryset = queryset.filter(show_time__date=parsed_date)

        if plays:
            play_ids = params_to_ints(plays)
            queryset = queryset.filter(play_id__in=play_ids)

        return queryset


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Reservation.objects.filter(user=self.request.user)
            .prefetch_related("tickets__performance")
            .order_by("id")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
