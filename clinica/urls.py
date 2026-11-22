"""Rutas RESTful del dominio clínico veterinario PetCare y Arquitectura AWS (Evaluación N.º 4)."""
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
    ArquitecturaAWSStatusView,
    S3PresignedUrlView,
    RateLimitDemoEndpointView,
    RateLimitResetView,
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
    path('aws/estado/', ArquitecturaAWSStatusView.as_view(), name='aws-estado'),
    path('aws/s3-presigned-url/', S3PresignedUrlView.as_view(), name='aws-s3-presigned-url'),
    path('aws/rate-limit-test/', RateLimitDemoEndpointView.as_view(), name='aws-rate-limit-test'),
    path('aws/rate-limit-reset/', RateLimitResetView.as_view(), name='aws-rate-limit-reset'),
    path('', include(router.urls)),
]
