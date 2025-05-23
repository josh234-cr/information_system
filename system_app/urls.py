from django.urls import path
from .views import institution_dashboard, register_refugee,auth_view
from .views import begin_registration, complete_registration
from .views import capture_face, authenticate_refugee
from .views import health_records,appointments

urlpatterns = [
    path("", auth_view, name="auth"),  # One URL for login & signup
    path('dashboard/', institution_dashboard, name='institution_dashboard'),
    path('register/', register_refugee, name='register_refugee'),
    path("register/begin/", begin_registration, name="begin_registration"),
    path("register/complete/", complete_registration, name="complete_registration"),
    path("capture/", capture_face, name="capture_face"),
    path("authenticate/", authenticate_refugee, name="authenticate_refugee"),
    path('health-records/', health_records, name='health_records'),
    path('appointments/', appointments, name='appointments'),
]