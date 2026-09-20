from django.urls import path

from .views import (
    home,

    # Citizen
    register_page,
    register_citizen,
    login_page,
    citizen_login,
    citizen_dashboard,
    citizen_logout,
    report_issue,
    submit_complaint,

    # Officer
    officer_login_page,
    officer_login,
    officer_dashboard,
    officer_logout,
)


urlpatterns = [

    # =====================================================
    # LANDING PAGE
    # =====================================================

    path(
        "",
        home,
        name="home"
    ),


    # =====================================================
    # CITIZEN REGISTRATION
    # =====================================================

    # Citizen registration page
    path(
        "register/",
        register_page,
        name="register"
    ),

    # Citizen registration form submit
    path(
        "register/citizen/",
        register_citizen,
        name="register_citizen"
    ),


    # =====================================================
    # CITIZEN LOGIN
    # =====================================================

    # Citizen login page
    path(
        "login/",
        login_page,
        name="login"
    ),

    # Citizen login form submit
    path(
        "login/citizen/",
        citizen_login,
        name="citizen_login"
    ),


    # =====================================================
    # CITIZEN DASHBOARD
    # =====================================================

    path(
        "citizen-dashboard/",
        citizen_dashboard,
        name="citizen_dashboard"
    ),


    # =====================================================
    # CITIZEN REPORT ISSUE
    # =====================================================

    path(
        "report_issue/",
        report_issue,
        name="report_issue"
    ),


    # =====================================================
    # SUBMIT COMPLAINT
    # =====================================================

    path(
        "submit_complaint/",
        submit_complaint,
        name="submit_complaint"
    ),


    # =====================================================
    # CITIZEN LOGOUT
    # =====================================================

    path(
        "logout/",
        citizen_logout,
        name="citizen_logout"
    ),


    # =====================================================
    # OFFICER LOGIN
    # =====================================================

    # Officer login page
    path(
        "officer/login/",
        officer_login_page,
        name="officer_login"
    ),

    # Officer login form submit
    path(
        "officer/login/submit/",
        officer_login,
        name="officer_login_submit"
    ),


    # =====================================================
    # OFFICER DASHBOARD
    # =====================================================

    path(
        "officer-dashboard/",
        officer_dashboard,
        name="officer_dashboard"
    ),


    # =====================================================
    # OFFICER LOGOUT
    # =====================================================

    path(
        "officer-logout/",
        officer_logout,
        name="officer_logout"
    ),

]

