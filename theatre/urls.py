from rest_framework import routers

from theatre.views import (
    ActorViewSet,
    GenreViewSet,
    PerformanceViewSet, PlayViewSet,
    TheatreHallViewSet
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("halls", TheatreHallViewSet)
router.register("plays", PlayViewSet)
router.register("performances", PerformanceViewSet)

urlpatterns = router.urls