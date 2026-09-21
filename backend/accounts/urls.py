from django.urls import path

from .views import (
    home,
    register_page,
    register_citizen,
    login_page,
    citizen_login,
    citizen_dashboard,
    citizen_logout,
    my_complaints,
    report_issue,
    submit_complaint,
)


urlpatterns = [
    # Landing page
    path("", home, name="home"),

    # Citizen registration page
    path("register/", register_page, name="register"),

    # Citizen registration form submit
    path("register/citizen/", register_citizen, name="register_citizen"),

    # Citizen login page
    path("login/", login_page, name="login"),

    # Citizen login form submit
    path("login/citizen/", citizen_login, name="citizen_login"),

    # Citizen dashboard
    path(
        "citizen-dashboard/",
        citizen_dashboard,
        name="citizen_dashboard"
    ),
    # My complaints
    path(
        "my-complaints/",
        my_complaints,
        name="my_complaints"
    ),
    # Report an issue
    path("report_issue/", report_issue, name="report_issue"),

    # Submit Complaints

    path("submit_complaint/",submit_complaint,name="submit_complaint"),
    # Logout
    path(
        "logout/",
        citizen_logout,
        name="citizen_logout"
    ),
]