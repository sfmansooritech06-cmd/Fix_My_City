from django.urls import path

from .views import (
    home,
    register_page,
    register_citizen,
    login_page,
    citizen_login,
    citizen_dashboard,
    citizen_logout,
    report_issue,
    submit_complaint,
    my_complaints,

    # Officer
    officer_register_page,
    officer_register,
    officer_login_page,
    officer_login,
    officer_logout,

    # Admin Officer Verification
    admin_officer_verification,
    approve_officer,
    reject_officer,

    # Admin login

    admin_login_page,
    admin_login,
    admin_dashboard,
    admin_logout

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
# Officer
path(
    "officer-register/",
    officer_register_page,
    name="officer_register"
),

path(
    "officer-register/submit/",
    officer_register,
    name="officer_register_submit"
),

path(
    "officer-login/",
    officer_login_page,
    name="officer_login"
),

path(
    "officer-login/submit/",
    officer_login,
    name="officer_login_submit"
),

path(
    "officer-logout/",
    officer_logout,
    name="officer_logout"
),

# Admin Officer Verification
path(
    "admin/officer-verification/",
    admin_officer_verification,
    name="admin_officer_verification"
),

path(
    "admin/approve-officer/<int:officer_id>/",
    approve_officer,
    name="approve_officer"
),

path(
    "admin/reject-officer/<int:officer_id>/",
    reject_officer,
    name="reject_officer"
),
path(
    "admin-login/",
    admin_login_page,
    name="admin_login"
),

path(
    "admin-login/submit/",
    admin_login,
    name="admin_login_submit"
),

path(
    "admin-dashboard/",
    admin_dashboard,
    name="admin_dashboard"
),
path(
    "admin-logout/",
    admin_logout,
    name="admin_logout"
),
]