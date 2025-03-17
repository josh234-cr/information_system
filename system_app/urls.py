from django.urls import path
from .views import institution_dashboard, register_refugee,auth_view
from .views import begin_registration, complete_registration

urlpatterns = [
    path("", auth_view, name="auth"),  # One URL for login & signup
    path('dashboard/', institution_dashboard, name='institution_dashboard'),
    path('register/', register_refugee, name='register_refugee'),
        path("register/begin/", begin_registration, name="begin_registration"),
    path("register/complete/", complete_registration, name="complete_registration"),
]