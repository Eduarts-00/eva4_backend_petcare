"""Rutas RESTful del dominio clínico veterinario PetCare."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfesionalViewSet,
    TutorViewSet,
    MascotaViewSet,
    CitaMedicaViewSet,
    FichaClinicaViewSet,
    ControlVacunaViewSet,
    DashboardResumenView,
)

router = DefaultRouter()
router.register(r'profesionales', ProfesionalViewSet, basename='profesionales')
router.register(r'tutores', TutorViewSet, basename='tutores')
router.register(r'mascotas', MascotaViewSet, basename='mascotas')
router.register(r'citas', CitaMedicaViewSet, basename='citas')
router.register(r'fichas-clinicas', FichaClinicaViewSet, basename='fichas-clinicas')
router.register(r'recordatorios', ControlVacunaViewSet, basename='recordatorios')

urlpatterns = [
    path('dashboard/resumen/', DashboardResumenView.as_view(), name='dashboard-resumen'),
    path('', include(router.urls)),
]
