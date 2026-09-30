from rest_framework import routers

from theatre.views import (
    ActorViewSet,
    GenreViewSet,
    PerformanceViewSet, PlayViewSet,
    ReservationViewSet, TheatreHallViewSet
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("halls", TheatreHallViewSet)
router.register("plays", PlayViewSet)
router.register("performances", PerformanceViewSet)
router.register(
    "reservations",
    ReservationViewSet,
    basename="reservation"
)

urlpatterns = router.urls