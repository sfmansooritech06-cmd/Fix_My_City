from django.urls import path
from . import views


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
    my_complaints,

   # Officer
    officer_register_page,
    officer_register,
    officer_login_page,
    officer_login,
    officer_dashboard,
    officer_complaints,
    officer_complaint_details,
    officer_logout,

    # Admin Verification & Login
    admin_officer_verification,
    approve_officer,
    reject_officer,
    admin_login_page,
    admin_login,
    admin_dashboard,
    admin_logout
)


urlpatterns = [

    # =====================================================
    # LANDING PAGE
    # =====================================================
    path("", home, name="home"),


    # =====================================================
    # CITIZEN REGISTRATION
    # =====================================================
    path("register/", register_page, name="register"),
    path("register/citizen/", register_citizen, name="register_citizen"),


    # =====================================================
    # CITIZEN LOGIN
    # =====================================================
    path("login/", login_page, name="login"),
    path("login/citizen/", citizen_login, name="citizen_login"),


    # =====================================================
    # CITIZEN DASHBOARD & ACTIONS
    # =====================================================
    path("citizen-dashboard/", citizen_dashboard, name="citizen_dashboard"),
    path("my-complaints/", my_complaints, name="my_complaints"),
    path("report_issue/", report_issue, name="report_issue"),
    path("submit_complaint/", submit_complaint, name="submit_complaint"),


    # =====================================================
    # CITIZEN LOGOUT
    # =====================================================
    path("logout/", citizen_logout, name="citizen_logout"),


    # =====================================================
    # OFFICER REGISTRATION & LOGIN
    # =====================================================
    path("officer-register/", officer_register_page, name="officer_register"),
    path("officer-register/submit/", officer_register, name="officer_register_submit"),
    path("officer-login/", officer_login_page, name="officer_login"),
    path("officer-login/submit/", officer_login, name="officer_login_submit"),


    # =====================================================
# OFFICER DASHBOARD & COMPLAINTS
# =====================================================

    path(
        "officer-dashboard/",
        officer_dashboard,
        name="officer_dashboard"
    ),

    path(
        "officer-complaints/",
        officer_complaints,
        name="officer_complaints"
    ),

    path(
        "officer-complaint-details/",
        officer_complaint_details,
        name="officer_complaint_details"
    ),

    path(
        "officer-logout/",
        officer_logout,
        name="officer_logout"
    ),


    # =====================================================
    # ADMIN: VERIFICATION
    # =====================================================
    path("admin/officer-verification/", admin_officer_verification, name="admin_officer_verification"),
    path("admin/approve-officer/<int:officer_id>/", approve_officer, name="approve_officer"),
    path("admin/reject-officer/<int:officer_id>/", reject_officer, name="reject_officer"),


    # =====================================================
    # ADMIN: LOGIN & DASHBOARD
    # =====================================================
    path("admin-login/", admin_login_page, name="admin_login"),
    path("admin-login/submit/", admin_login, name="admin_login_submit"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin-logout/", admin_logout, name="admin_logout"),
    
    path(
    'officer/complaint/<str:complaint_id>/progress/',
    views.update_complaint_progress,
    name='update_complaint_progress'
),

]