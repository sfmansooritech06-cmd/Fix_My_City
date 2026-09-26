from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import User, Citizen, Officer, Complaint

import os
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# =====================================================
# LANDING PAGE
# =====================================================

def home(request):
    return render(request, "index.html")


# =====================================================
# CITIZEN REGISTER PAGE
# =====================================================

def register_page(request):
    return render(request, "register.html")


# =====================================================
# CITIZEN REGISTER
# =====================================================

@require_POST
def register_citizen(request):
    full_name = request.POST.get("full_name", "").strip()
    email = request.POST.get("email", "").strip().lower()
    phone = request.POST.get("phone", "").strip()
    password = request.POST.get("password", "")
    confirm_password = request.POST.get("confirm_password", "")

    # Required fields
    if not full_name or not email or not phone or not password:
        return JsonResponse({
            "success": False,
            "message": "All fields are required."
        }, status=400)

    # Password check
    if password != confirm_password:
        return JsonResponse({
            "success": False,
            "message": "Passwords do not match."
        }, status=400)

    # Email already exists
    if User.objects.filter(email=email).exists():
        return JsonResponse({
            "success": False,
            "message": "Email already registered."
        }, status=400)

    # Generate username internally
    username = email.split("@")[0]
    original_username = username
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{original_username}{counter}"
        counter += 1

    # Create User
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role="citizen"
    )

    # Generate Citizen ID
    last_citizen = Citizen.objects.order_by("-id").first()

    if last_citizen:
        next_number = last_citizen.id + 1
    else:
        next_number = 1

    citizen_id = f"FMC-CIT-{next_number:06d}"

    # Create Citizen profile
    citizen = Citizen.objects.create(
        user=user,
        citizen_id=citizen_id,
        full_name=full_name,
        phone=phone
    )
    return redirect("/citizen-dashboard/")


# =====================================================
# CITIZEN LOGIN PAGE
# =====================================================

def login_page(request):
    return render(request, "login.html")


# =====================================================
# CITIZEN LOGIN
# =====================================================

def citizen_login(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST method is allowed."
        }, status=405)

    login_value = request.POST.get("login_value", "").strip()
    password = request.POST.get("password", "")

    if not login_value or not password:
        return JsonResponse({
            "success": False,
            "message": "Please enter login details."
        }, status=400)

    user = None

    # Login using Citizen ID
    citizen = Citizen.objects.filter(
        citizen_id__iexact=login_value
    ).first()

    if citizen:
        user = citizen.user
    # Login using Email
    else:
        user = User.objects.filter(
            email__iexact=login_value,
            role="citizen"
        ).first()

    # Password verification
    if user and user.check_password(password):
        if not user.is_active:
            return JsonResponse({
                "success": False,
                "message": "Your account is inactive."
            }, status=403)


        login(request, user)

        return redirect("/citizen-dashboard/")

    return JsonResponse({
        "success": False,
        "message": "Invalid email/citizen ID or password."
    }, status=401)


# =====================================================
# CITIZEN DASHBOARD
# =====================================================

def citizen_dashboard(request):

    # Check login
    if not request.user.is_authenticated:
        return redirect("/login/")

    # Only citizen can access citizen dashboard
    if request.user.role != "citizen":
        return redirect("/login/")

    # Get logged-in citizen profile
    citizen = request.user.citizen_profile

    # All complaints of logged-in citizen
    complaints = Complaint.objects.filter(
        citizen=citizen
    ).order_by("-created_at")

    # =====================================================
    # DASHBOARD COUNTS
    # =====================================================

    total_complaints = complaints.count()

    in_progress_count = complaints.filter(
        status="in_progress"
    ).count()

    resolved_count = complaints.filter(
        status="resolved"
    ).count()

    # =====================================================
    # RECENT COMPLAINTS
    # =====================================================

    # Latest 3 complaints
    recent_complaints = complaints[:3]

    # Latest complaint for status tracking
    latest_complaint = complaints.first()

    # =====================================================
    # GENERATE CITIZEN INITIALS
    # =====================================================

    name_parts = citizen.full_name.strip().split()

    if len(name_parts) >= 2:
        # First name + Last name
        initials = (
            name_parts[0][0] +
            name_parts[-1][0]
        )
    elif len(name_parts) == 1:
        # Only one name
        initials = name_parts[0][0]
    else:
        # Fallback
        initials = "C"

    initials = initials.upper()

    # =====================================================
    # DASHBOARD DATA
    # =====================================================

    return render(
        request,
        "citizen_dashboard.html",
        {
            "citizen": citizen,
            "initials": initials,

            "total_complaints": total_complaints,

            "in_progress_count": in_progress_count,

            "resolved_count": resolved_count,

            "recent_complaints": recent_complaints,

            "latest_complaint": latest_complaint,

            # Upvote system abhi implement nahi hua hai
            "my_upvotes": 0,
        }
    )


# =====================================================
# MY COMPLAINTS
# =====================================================

def my_complaints(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    if request.user.role != "citizen":
        return redirect("/login/")

    citizen = request.user.citizen_profile

    # Get only this citizen's complaints
    complaints = Complaint.objects.filter(
        citizen=citizen
    ).order_by("-created_at")

    # Summary counts
    total_complaints = complaints.count()
    reported_count = complaints.filter(status="reported").count()
    in_progress_count = complaints.filter(status="in_progress").count()
    resolved_count = complaints.filter(status="resolved").count()

    return render(
        request,
        "my_complaints.html",
        {
            "citizen": citizen,
            "complaints": complaints,
            "total_complaints": total_complaints,
            "reported_count": reported_count,
            "in_progress_count": in_progress_count,
            "resolved_count": resolved_count,
        }
    )


# =====================================================
# OFFICER REGISTER PAGE
# =====================================================

def officer_register_page(request):
    return render(request, "officer_register.html")


# =====================================================
# OFFICER REGISTER
# =====================================================

@require_POST
def officer_register(request):
    full_name = request.POST.get("full_name", "").strip()
    employee_id = request.POST.get("employee_id", "").strip().upper()
    email = request.POST.get("email", "").strip().lower()
    phone = request.POST.get("phone", "").strip()
    department = request.POST.get("department", "").strip()
    password = request.POST.get("password", "")
    confirm_password = request.POST.get("confirm_password", "")

    # Required fields
    if not all([full_name, employee_id, email, phone, department, password, confirm_password]):
        return JsonResponse({
            "success": False,
            "message": "All fields are required."
        }, status=400)

    # Employee ID validation
    if not employee_id.isalnum() or len(employee_id) > 10:
        return JsonResponse({
            "success": False,
            "message": "Employee ID must contain only letters and numbers and cannot exceed 10 characters."
        }, status=400)

    # Phone validation
    if not phone.isdigit() or len(phone) != 10:
        return JsonResponse({
            "success": False,
            "message": "Please enter a valid 10-digit phone number."
        }, status=400)

    # Password validation
    if password != confirm_password:
        return JsonResponse({
            "success": False,
            "message": "Passwords do not match."
        }, status=400)

    if len(password) < 8:
        return JsonResponse({
            "success": False,
            "message": "Password must contain at least 8 characters."
        }, status=400)

    # Duplicate checks
    if Officer.objects.filter(employee_id__iexact=employee_id).exists():
        return JsonResponse({
            "success": False,
            "message": "Employee ID is already registered."
        }, status=400)

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({
            "success": False,
            "message": "Email is already registered."
        }, status=400)

    # Employee ID is used as username because officer login uses Employee ID
    if User.objects.filter(username__iexact=employee_id).exists():
        return JsonResponse({
            "success": False,
            "message": "Employee ID is already in use."
        }, status=400)

    # Create User account in pending state
    user = User.objects.create_user(
        username=employee_id,
        email=email,
        password=password,
        
        role="officer"
    )

    # Officer remains blocked until admin approves
    officer = Officer.objects.create(
        user=user,
        employee_id=employee_id,
        full_name=full_name,
        phone=phone,
        department=department,
        is_approved=False
    )

    return JsonResponse({
        "success": True,
        "message": "Officer registration submitted. Your account is pending admin verification.",
        "employee_id": officer.employee_id
    }, status=201)


# =====================================================
# OFFICER LOGIN PAGE
# =====================================================

def officer_login_page(request):
    return render(request, "officer_login.html")


# =====================================================
# OFFICER LOGIN
# =====================================================

def officer_login(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST method is allowed."
        }, status=405)

    # Get login details from HTML form
    employee_id = request.POST.get("employee_id", "").strip()
    password = request.POST.get("password", "")

    # Check empty fields
    if not employee_id or not password:
        return JsonResponse({
            "success": False,
            "message": "Please enter Employee ID and Password."
        }, status=400)

    # Find officer using Employee ID
    try:
        officer = Officer.objects.select_related("user").get(employee_id__iexact=employee_id)
    except Officer.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Invalid Employee ID or Password."
        }, status=401)

    # Check officer approval
    if not officer.is_approved:
        return JsonResponse({
            "success": False,
            "message": "Your officer account has not been approved yet."
        }, status=403)

    # Check whether linked User account is active
    if not officer.user.is_active:
        return JsonResponse({
            "success": False,
            "message": "Your officer account is inactive."
        }, status=403)

    # Authenticate using Django User password
    user = authenticate(
        request,
        username=officer.user.username,
        password=password
    )

    # Password incorrect
    if user is None:
        return JsonResponse({
            "success": False,
            "message": "Invalid Employee ID or Password."
        }, status=401)

    # Successful login
    login(request, user)

    return redirect("/officer-dashboard/")


# =====================================================
# OFFICER DASHBOARD
# =====================================================

def officer_dashboard(request):

    # User must be logged in
    if not request.user.is_authenticated:
        return redirect("/officer-login/")

    # Only officer can access
    if request.user.role != "officer":
        return redirect("/officer-login/")

    # Get officer profile
    try:
        officer = request.user.officer_profile
    except Officer.DoesNotExist:
        logout(request)
        return redirect("/officer-login/")

    # Officer must be approved
    if not officer.is_approved:
        logout(request)
        return redirect("/officer-login/")

    # =================================================
    # GET ASSIGNED COMPLAINTS
    # =================================================

    complaints = (
        Complaint.objects
        .select_related("citizen", "assigned_officer")
        .filter(
            assigned_officer=officer
        )
        .order_by("-created_at")
    )

    # =================================================
    # DASHBOARD COUNTS
    # =================================================

    total_assigned = complaints.count()

    pending_count = complaints.filter(
        status="reported"
    ).count()

    in_progress_count = complaints.filter(
        status="in_progress"
    ).count()

    resolved_count = complaints.filter(
        status="resolved"
    ).count()

    # =================================================
    # RECENT COMPLAINTS
    # =================================================

    recent_complaints = complaints[:3]

    # =================================================
    # PRIORITY COMPLAINTS
    # Highest upvotes first
    # =================================================

    priority_complaints = complaints.order_by(
        "-upvotes",
        "-created_at"
    )[:3]

    # =================================================
    # OFFICER INITIALS
    # =================================================

    name_parts = officer.full_name.strip().split()

    if len(name_parts) >= 2:
        initials = (
            name_parts[0][0]
            + name_parts[-1][0]
        )
    elif len(name_parts) == 1:
        initials = name_parts[0][0]
    else:
        initials = "O"

    initials = initials.upper()

    # =================================================
    # SEND DATA TO TEMPLATE
    # =================================================

    return render(
        request,
        "officer_dashboard.html",
        {
            "officer": officer,
            "initials": initials,

            "total_assigned": total_assigned,
            "pending_count": pending_count,
            "in_progress_count": in_progress_count,
            "resolved_count": resolved_count,

            # All assigned complaints
            "assigned_complaints": complaints,

            # Existing dashboard sections
            "recent_complaints": recent_complaints,
            "priority_complaints": priority_complaints,
        }
    )
    # =====================================================
# UPDATE COMPLAINT STATUS - OFFICER
# =====================================================

@require_POST
def update_complaint_status(request, complaint_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "message": "Authentication required."
        }, status=401)

    if request.user.role != "officer":
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    try:
        officer = request.user.officer_profile
    except Officer.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Officer profile not found."
        }, status=404)

    try:
        complaint = Complaint.objects.get(
            id=complaint_id,
            assigned_officer=officer
        )
    except Complaint.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Complaint is not assigned to you."
        }, status=404)

    status_value = request.POST.get("status")

    allowed_statuses = [
        "reported",
        "in_progress",
        "resolved"
    ]

    if status_value not in allowed_statuses:
        return JsonResponse({
            "success": False,
            "message": "Invalid complaint status."
        }, status=400)

    complaint.status = status_value

    complaint.save(
        update_fields=[
            "status",
            "updated_at"
        ]
    )

    return JsonResponse({
        "success": True,
        "message": "Complaint status updated successfully.",
        "status": complaint.get_status_display()
    })

def officer_complaints(request):
    if not request.user.is_authenticated:
        return redirect("/officer-login/")

    if request.user.role != "officer":
        return redirect("/officer-login/")

    try:
        officer = request.user.officer_profile
    except Officer.DoesNotExist:
        logout(request)
        return redirect("/officer-login/")

    if not officer.is_approved:
        logout(request)
        return redirect("/officer-login/")

    complaints = Complaint.objects.filter(
        assigned_officer=officer
    ).order_by("-created_at")

    total_count = complaints.count()

    reported_count = complaints.filter(
        status="reported"
    ).count()

    in_progress_count = complaints.filter(
        status="in_progress"
    ).count()

    resolved_count = complaints.filter(
        status="resolved"
    ).count()

    # Officer initials
    name_parts = officer.full_name.strip().split()

    if len(name_parts) >= 2:
        initials = (
            name_parts[0][0] +
            name_parts[-1][0]
        )

    elif len(name_parts) == 1:
        initials = name_parts[0][0]

    else:
        initials = "O"

    initials = initials.upper()

    return render(
        request,
        "officer_complaints.html",
        {
            "officer": officer,
            "initials": initials,

            "complaints": complaints,

            "total_count": total_count,
            "reported_count": reported_count,
            "in_progress_count": in_progress_count,
            "resolved_count": resolved_count,

            "category_choices": Complaint.CATEGORY_CHOICES,
        }
    )
# =====================================================
# OFFICER COMPLAINT DETAILS
# =====================================================

def officer_complaint_details(request, complaint_id):

    if not request.user.is_authenticated:
        return redirect("/officer-login/")

    if request.user.role != "officer":
        return redirect("/officer-login/")

    try:
        officer = request.user.officer_profile
    except Officer.DoesNotExist:
        logout(request)
        return redirect("/officer-login/")

    if not officer.is_approved:
        logout(request)
        return redirect("/officer-login/")

    try:
        complaint = (
            Complaint.objects
            .select_related("citizen", "assigned_officer")
            .get(
                id=complaint_id,
                assigned_officer=officer
            )
        )
    except Complaint.DoesNotExist:
        return redirect("/officer-complaints/")

    return render(
        request,
        "officer_complaint_details.html",
        {
            "officer": officer,
            "complaint": complaint,
        }
    )


# =====================================================
# OFFICER LOGOUT
# =====================================================

def officer_logout(request):
    logout(request)
    return redirect("/officer-login/")


# =====================================================
# CITIZEN LOGOUT
# =====================================================

def citizen_logout(request):
    logout(request)
    return redirect("/login/")


# =====================================================
# REPORT ISSUE
# =====================================================

def report_issue(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    if request.user.role != "citizen":
        return redirect("/login/")

    citizen = request.user.citizen_profile
    name_parts = citizen.full_name.strip().split()

    if len(name_parts) >= 2:
        initials = name_parts[0][0] + name_parts[1][0]
    else:
        initials = name_parts[0][0]

    return render(
        request,
        "report_issue.html",
        {
            "citizen": citizen,
            "initials": initials.upper(),
        }
    )


# =====================================================
# SUBMIT COMPLAINT
# =====================================================

def submit_complaint(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    if request.user.role != "citizen":
        return redirect("/login/")

    if request.method != "POST":
        return redirect("/report_issue/")

    citizen = request.user.citizen_profile

    category = request.POST.get("category", "").strip()
    title = request.POST.get("issue_title", "").strip()
    description = request.POST.get("description", "").strip()
    address = request.POST.get("location", "").strip()
    latitude = request.POST.get("latitude", "").strip()
    longitude = request.POST.get("longitude", "").strip()
    photo = request.FILES.get("issue_photo")

    # Required text fields
    if not category or not title or not description or not address:
        return JsonResponse({
            "success": False,
            "message": "Please fill all required fields."
        }, status=400)

    # -----------------------------------------------------
    # PHOTO VALIDATION
    # -----------------------------------------------------
    if not photo:
        return JsonResponse({
            "success": False,
            "message": "Please upload a photo of the issue."
        }, status=400)

    extension = os.path.splitext(photo.name)[1].lower().lstrip(".")

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return JsonResponse({
            "success": False,
            "message": "Only JPG, JPEG or PNG image files are allowed."
        }, status=400)

    if photo.size > MAX_IMAGE_SIZE_BYTES:
        return JsonResponse({
            "success": False,
            "message": "Image size must not exceed 5 MB."
        }, status=400)

    try:
        img = Image.open(photo)
        img.verify()
    except (UnidentifiedImageError, IOError, SyntaxError):
        return JsonResponse({
            "success": False,
            "message": "The uploaded file is not a valid image or is corrupted."
        }, status=400)

    photo.seek(0)

    try:
        img_check = Image.open(photo)
        if img_check.format not in ALLOWED_IMAGE_FORMATS:
            return JsonResponse({
                "success": False,
                "message": "Only JPG, JPEG or PNG image files are allowed."
            }, status=400)
    except (UnidentifiedImageError, IOError, SyntaxError):
        return JsonResponse({
            "success": False,
            "message": "The uploaded file is not a valid image or is corrupted."
        }, status=400)

    photo.seek(0)

    # -----------------------------------------------------
    # END PHOTO VALIDATION
    # -----------------------------------------------------

    # Generate complaint ID
    last_complaint = Complaint.objects.order_by("-id").first()
    if last_complaint:
        next_number = last_complaint.id + 1
    else:
        next_number = 1

    complaint_id = f"FMC-CMP-{next_number:06d}"

    # Create complaint
    complaint = Complaint.objects.create(
        complaint_id=complaint_id,
        citizen=citizen,
        category=category,
        title=title,
        description=description,
        photo=photo,
        address=address,
        latitude=latitude if latitude else None,
        longitude=longitude if longitude else None,
        status="reported"
    )

    messages.success(
    request,
    f"Your complaint has been successfully submitted. Complaint ID: {complaint.complaint_id}"
    )

    return redirect("citizen_dashboard")


# =====================================================
# ADMIN LOGIN PAGE
# =====================================================

def admin_login_page(request):
    return render(request, "admin_login.html")


# =====================================================
# ADMIN LOGIN
# =====================================================

@require_POST
def admin_login(request):

    admin_id = request.POST.get("admin_id", "").strip()
    password = request.POST.get("password", "")

    # Empty fields
    if not admin_id or not password:
        return render(
            request,
            "admin_login.html",
            {
                "error": "Please enter Admin ID and password."
            }
        )

    # Find admin user
    try:
        user = User.objects.get(username=admin_id)

    except User.DoesNotExist:
        return render(
            request,
            "admin_login.html",
            {
                "error": "Invalid Admin ID or password."
            }
        )

    # Check admin role
    if user.role != "admin":
        return render(
            request,
            "admin_login.html",
            {
                "error": "You are not authorized as an admin."
            }
        )

    # Authenticate password
    authenticated_user = authenticate(
        request,
        username=user.username,
        password=password
    )

    if authenticated_user is None:
        return render(
            request,
            "admin_login.html",
            {
                "error": "Invalid Admin ID or password."
            }
        )

    # Check active account
    if not user.is_active:
        return render(
            request,
            "admin_login.html",
            {
                "error": "Your admin account is inactive."
            }
        )

    # Login user
    login(request, authenticated_user)

    # Direct dashboard redirect
    return redirect("/admin-dashboard/")


# =====================================================
# ADMIN OFFICER VERIFICATION
# =====================================================

def admin_officer_verification(request):

    if not request.user.is_authenticated:
        return redirect("/admin-login/")

    if request.user.role != "admin":
        return redirect("/admin-login/")

    pending_officers_qs = Officer.objects.filter(
        is_approved=False
    ).select_related("user").order_by("-created_at")

    pending_officers = []

    for officer in pending_officers_qs:

        name_parts = officer.full_name.strip().split()

        if len(name_parts) >= 2:
            initials = (
                name_parts[0][0] +
                name_parts[-1][0]
            ).upper()

        elif name_parts:
            initials = name_parts[0][0].upper()

        else:
            initials = "?"

        pending_officers.append({
            "id": officer.id,
            "initials": initials,
            "full_name": officer.full_name,
            "employee_id": officer.employee_id,
            "email": officer.user.email,
            "phone": officer.phone,
            "department": officer.get_department_display(),
            "created_at": officer.created_at,
        })

    admin_name = (
        request.user.get_full_name()
        or request.user.username
    )

    name_parts = admin_name.strip().split()

    if len(name_parts) >= 2:
        admin_initials = (
            name_parts[0][0] +
            name_parts[1][0]
        ).upper()

    elif name_parts:
        admin_initials = name_parts[0][0].upper()

    else:
        admin_initials = "A"

    return render(
        request,
        "admin_officer_verification.html",
        {
            "pending_officers": pending_officers,
            "pending_count": len(pending_officers),
            "admin_name": admin_name,
            "admin_initials": admin_initials,
        }
    )


# =====================================================
# ADMIN DASHBOARD
# =====================================================

def admin_dashboard(request):

    if not request.user.is_authenticated:
        return redirect("/admin-login/")

    if request.user.role != "admin":
        return redirect("/admin-login/")

    admin_name = request.user.username
    if request.user.first_name:
        admin_name = request.user.first_name

    admin_initials = request.user.username[:2].upper()

    pending_officer_requests = (
        Officer.objects
        .select_related("user")
        .filter(is_approved=False)
        .order_by("-created_at")
    )

    pending_requests_count = pending_officer_requests.count()

    approved_officers = (
        Officer.objects
        .select_related("user")
        .filter(is_approved=True)
        .order_by("full_name")
    )

    approved_officers_count = approved_officers.count()

    department_stats = []
    for department_code, department_name in Officer.DEPARTMENT_CHOICES:
        count = Officer.objects.filter(
            department=department_code,
            is_approved=True
        ).count()

        department_stats.append({
            "name": department_name,
            "code": department_code,
            "count": count
        })

    total_complaints_count = Complaint.objects.count()
    reported_count = Complaint.objects.filter(status="reported").count()
    in_progress_count = Complaint.objects.filter(status="in_progress").count()
    resolved_count = Complaint.objects.filter(status="resolved").count()
    unassigned_count = Complaint.objects.filter(
        assigned_officer__isnull=True
    ).count()

    unassigned_complaints = (
        Complaint.objects
        .select_related("citizen")
        .filter(assigned_officer__isnull=True)
        .order_by("-created_at")
    )

    assigned_complaints = (
        Complaint.objects
        .select_related("citizen", "assigned_officer")
        .filter(assigned_officer__isnull=False)
        .order_by("-updated_at")
    )

    assignment_complaints_data = []
    for complaint in unassigned_complaints:
        assignment_complaints_data.append({
            "id": complaint.id,
            "complaint_id": complaint.complaint_id,
            "title": complaint.title,
            "category": complaint.category,
            "category_name": complaint.get_category_display(),
            "address": complaint.address,
            "citizen_name": complaint.citizen.full_name,
            "created_at": complaint.created_at.strftime("%d %b %Y, %I:%M %p"),
        })

    citizens = (
        Citizen.objects
        .select_related("user")
        .prefetch_related("complaints")
        .order_by("-id")
    )

    citizen_list = []
    for citizen in citizens:
        complaints = list(citizen.complaints.all())
        categories = []

        for complaint in complaints:
            category = complaint.get_category_display()
            if category not in categories:
                categories.append(category)

        citizen_list.append({
            "id": citizen.id,
            "full_name": citizen.full_name,
            "citizen_id": citizen.citizen_id,
            "email": citizen.user.email,
            "phone": citizen.phone,
            "categories": categories,
            "complaint_count": len(complaints),
            "created_at": citizen.user.date_joined,
        })

    total_citizens_count = len(citizen_list)

    recent_complaints = (
        Complaint.objects
        .select_related("citizen", "assigned_officer")
        .order_by("-created_at")[:10]
    )

    recent_activity = []
    for complaint in recent_complaints:
        recent_activity.append({
            "type": "complaint",
            "title": f"New complaint reported by {complaint.citizen.full_name}",
            "description": complaint.title,
            "complaint_id": complaint.complaint_id,
            "status": complaint.get_status_display(),
            "created_at": complaint.created_at,
        })

    context = {
        "admin_name": admin_name,
        "admin_initials": admin_initials,
        "pending_requests_count": pending_requests_count,
        "approved_officers_count": approved_officers_count,
        "pending_officer_requests": pending_officer_requests,
        "approved_officers": approved_officers,
        "department_stats": department_stats,
        "total_complaints_count": total_complaints_count,
        "reported_count": reported_count,
        "in_progress_count": in_progress_count,
        "resolved_count": resolved_count,
        "unassigned_count": unassigned_count,
        "unassigned_complaints": unassigned_complaints,
        "assigned_complaints": assigned_complaints,
        "assignment_complaints_data": assignment_complaints_data,
        "recent_complaints": recent_complaints,
        "citizens": citizen_list,
        "total_citizens_count": total_citizens_count,
        "recent_activity": recent_activity,
    }

    return render(request, "admin_dashboard.html", context)


def admin_category_view(request, department_code):

    # Admin authentication
    if not request.user.is_authenticated:
        return redirect("/admin-login/")

    if request.user.role != "admin":
        return redirect("/admin-login/")

    # Check valid department
    department_dict = dict(Officer.DEPARTMENT_CHOICES)

    if department_code not in department_dict:
        return redirect("/admin-dashboard/")

    department_name = department_dict[department_code]

    # Approved officers of selected department
    officers = (
        Officer.objects
        .select_related("user")
        .filter(
            department=department_code,
            is_approved=True
        )
        .order_by("full_name")
    )

    # Find complaint categories belonging to this department
    complaint_categories = [
        category_code
        for category_code, department in CATEGORY_DEPARTMENT_MAP.items()
        if department == department_code
    ]

    # Unassigned complaints for this department/category
    complaints = (
        Complaint.objects
        .select_related("citizen", "assigned_officer")
        .filter(
            category__in=complaint_categories,
            assigned_officer__isnull=True
        )
        .order_by("-created_at")
    )

    # Already assigned complaints
    assigned_complaints = (
        Complaint.objects
        .select_related("citizen", "assigned_officer")
        .filter(
            category__in=complaint_categories,
            assigned_officer__isnull=False
        )
        .order_by("-updated_at")
    )

    context = {
        "department_code": department_code,
        "department_name": department_name,

        "officers": officers,
        "officer_count": officers.count(),

        "complaints": complaints,
        "complaint_count": complaints.count(),

        "assigned_complaints": assigned_complaints,
    }

    return render(
        request,
        "admin_category.html",
        context
    )


# =========================================================
# ADMIN - ASSIGN COMPLAINT
# =========================================================

@require_POST
def assign_complaint(request, complaint_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "message": "Authentication required."
        }, status=401)

    if request.user.role != "admin":
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    officer_id = request.POST.get("officer_id")

    if not officer_id:
        return JsonResponse({
            "success": False,
            "message": "Please select an officer."
        }, status=400)

    try:
        complaint = Complaint.objects.select_related("citizen").get(
            id=complaint_id
        )
    except Complaint.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Complaint not found."
        }, status=404)

    try:
        officer = Officer.objects.get(
            id=officer_id,
            is_approved=True
        )
    except Officer.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Approved officer not found."
        }, status=404)

    required_department = CATEGORY_DEPARTMENT_MAP.get(
        complaint.category
    )

    if required_department != officer.department:
        return JsonResponse({
            "success": False,
            "message": "This officer does not belong to the required department."
        }, status=400)

    complaint.assigned_officer = officer

    if complaint.status == "reported":
        complaint.status = "in_progress"

    complaint.save(update_fields=[
        "assigned_officer",
        "status",
        "updated_at"
    ])

    return JsonResponse({
        "success": True,
        "message": "Complaint assigned successfully.",
        "complaint_id": complaint.complaint_id,
        "officer_name": officer.full_name,
        "citizen_name": complaint.citizen.full_name,
        "status": complaint.get_status_display(),
    })


# =====================================================
# ADMIN - APPROVE OFFICER
# =====================================================

@require_POST
def approve_officer(request, officer_id):

    # Check admin login
    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "message": "Authentication required."
        }, status=401)

    # Only admin can approve officers
    if request.user.role != "admin":
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    # Find officer
    try:
        officer = Officer.objects.get(id=officer_id)

    except Officer.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Officer not found."
        }, status=404)

    # Approve officer
    officer.is_approved = True
    officer.save(update_fields=["is_approved"])

    return JsonResponse({
        "success": True,
        "message": "Officer approved successfully."
    })


# =====================================================
# ADMIN - REJECT OFFICER
# =====================================================

@require_POST
def reject_officer(request, officer_id):

    # Check admin login
    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "message": "Authentication required."
        }, status=401)

    # Only admin can reject officers
    if request.user.role != "admin":
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    # Find officer
    try:
        officer = Officer.objects.select_related("user").get(
            id=officer_id
        )

    except Officer.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Officer not found."
        }, status=404)

    # Delete officer and linked user account
    user = officer.user

    officer.delete()
    user.delete()

    return JsonResponse({
        "success": True,
        "message": "Officer registration rejected."
    })

# =====================================================
# ADMIN - ASSIGN COMPLAINT TO OFFICER
# =====================================================

@require_POST
def assign_complaint(request, complaint_id):

    if not request.user.is_authenticated:
        return JsonResponse({
            "success": False,
            "message": "Authentication required."
        }, status=401)

    if request.user.role != "admin":
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    try:
        complaint = Complaint.objects.get(id=complaint_id)
    except Complaint.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Complaint not found."
        }, status=404)

    officer_id = request.POST.get("officer_id")

    if not officer_id:
        return JsonResponse({
            "success": False,
            "message": "Please select an officer."
        }, status=400)

    try:
        officer = Officer.objects.get(
            id=officer_id,
            is_approved=True
        )
    except Officer.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Approved officer not found."
        }, status=404)

    complaint.assigned_officer = officer
    complaint.save(
        update_fields=[
            "assigned_officer",
            "updated_at"
        ]
    )

    return JsonResponse({
        "success": True,
        "message": (
            f"Complaint {complaint.complaint_id} "
            f"assigned to {officer.full_name}."
        )
    })

# =====================================================
# ADMIN LOGOUT
# =====================================================

def admin_logout(request):
    logout(request)
    return redirect("/admin-login/")

#=====================================================
#Progress Update for Complaint
#=====================================================

def update_complaint_progress(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        progress = request.POST.get("progress")

        if progress:
            complaint.progress = int(progress)
            complaint.save()

            messages.success(
                request,
                "Complaint progress updated successfully."
            )

    return redirect("officer_dashboard")