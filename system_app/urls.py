from django.urls import path
from .views import institution_dashboard, register_refugee
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import generate_fingerprint_challenge

urlpatterns = [
    path('dashboard/', institution_dashboard, name='institution_dashboard'),
    path('register/', register_refugee, name='register_refugee'),
    path('register/', register_refugee, name='register_refugee'),
    path("api/generate_fingerprint_challenge/", generate_fingerprint_challenge, name="generate_fingerprint_challenge"),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]