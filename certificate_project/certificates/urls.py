from django.urls import path
from . import views

urlpatterns = [
    path("admin-login/", views.admin_login, name="admin_login"),
    path("student/login/", views.student_login, name="student_login"),
    path("third-party/", views.third_party, name="third_party"),
    path("admin-login/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path(
        "student/dashboard/<int:student_id>/",
        views.student_dashboard,
        name="student_dashboard",
    ),
    path("student/register/", views.student_register, name="student_register"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "download-certificate/<str:student_name>/",
        views.download_certificate,
        name="download_certificate",
    ),
    path("verify-certificate/", views.verify_certificate, name="verify_cert"),
]
