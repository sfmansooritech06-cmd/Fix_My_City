import os

from PIL import Image, UnidentifiedImageError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import User, Citizen, Officer, Complaint


# =========================================================
# CONSTANTS
# =========================================================

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


# =========================================================
# CATEGORY → DEPARTMENT MAPPING
# =========================================================
#
# IMPORTANT:
# Replace these values with the EXACT category and department
# codes used in your models.py.
#
# Example:
#
# CATEGORY_DEPARTMENT_MAP = {
#     "pothole": "roads",
#     "street_light": "electricity",
#     "water_leakage": "water",
# }
#
# If you already define CATEGORY_DEPARTMENT_MAP somewhere else,
# import it instead and remove this section.
# =========================================================

CATEGORY_DEPARTMENT_MAP = {
    # "pothole": "roads",
    # "street_light": "electricity",
    # "water_leakage": "water",
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def citizen_required(request):
    """
    Check whether the current user is an authenticated citizen.
    Returns Citizen profile if valid, otherwise None.
    """

    if not request.user.is_authenticated:
        return None

    if getattr(request.user, "role", None) != "citizen":
        return None

    try:
        return request.user.citizen_profile
    except Citizen.DoesNotExist:
        return None


def officer_required(request):
    """
    Check whether the current user is an authenticated,
    approved officer.
    """

    if not request.user.is_authenticated:
        return None

    if getattr(request.user, "role", None) != "officer":
        return None

    try:
        officer = request.user.officer_profile
    except Officer.DoesNotExist:
        return None

    if not officer.is_approved:
        return None

    if not request.user.is_active:
        return None

    return officer


def admin_required(request):
    """
    Check whether the current user is an authenticated admin.
    """

    if not request.user.is_authenticated:
        return False

    if getattr(request.user, "role", None) != "admin":
        return False

    if not request.user.is_active:
        return False

    return True


def get_initials(name, fallback="U"):
    """
    Generate initials from a person's name.
    """

    name = (name or "").strip()

    if not name:
        return fallback.upper()

    parts = name.split()

    if len(parts) >= 2:
        return (
            parts[0][0] +
            parts[-1][0]
        ).upper()

    return parts[0][0].upper()


def validate_uploaded_image(photo):
    """
    Validate uploaded complaint image.

    Returns:
        (True, None) if valid
        (False, error_message) if invalid
    """

    if not photo:
        return False, "Please upload a photo of the issue."

    extension = (
        os.path.splitext(photo.name)[1]
        .lower()
        .lstrip(".")
    )

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return (
            False,
            "Only JPG, JPEG or PNG image files are allowed."
        )

    if photo.size > MAX_IMAGE_SIZE_BYTES:
        return (
            False,
            "Image size must not exceed 5 MB."
        )

    try:
        image = Image.open(photo)
        image.verify()
    except (
        UnidentifiedImageError,
        IOError,
        SyntaxError
    ):
        return (
            False,
            "The uploaded file is not a valid image or is corrupted."
        )

    photo.seek(0)

    try:
        image_check = Image.open(photo)

        if image_check.format not in ALLOWED_IMAGE_FORMATS:
            return (
                False,
                "Only JPG, JPEG or PNG image files are allowed."
            )

        image_check.close()

    except (
        UnidentifiedImageError,
        IOError,
        SyntaxError
    ):
        return (
            False,
            "The uploaded file is not a valid image or is corrupted."
        )

    photo.seek(0)

    return True, None


def get_next_citizen_id():
    """
    Generate next citizen ID.

    Format:
    FMC-CIT-000001
    """

    last_citizen = (
        Citizen.objects
        .order_by("-id")
        .first()
    )

    next_number = (
        last_citizen.id + 1
        if last_citizen
        else 1
    )

    return f"FMC-CIT-{next_number:06d}"


def get_next_complaint_id():
    """
    Generate next complaint ID.

    Format:
    FMC-CMP-000001
    """

    last_complaint = (
        Complaint.objects
        .order_by("-id")
        .first()
    )

    next_number = (
        last_complaint.id + 1
        if last_complaint
        else 1
    )

    return f"FMC-CMP-{next_number:06d}"


# =========================================================
# LANDING PAGE
# =========================================================

def home(request):
    return render(request, "index.html")


# =========================================================
# CITIZEN REGISTER PAGE
# =========================================================

def register_page(request):
    return render(request, "register.html")


# =========================================================
# CITIZEN REGISTER
# =========================================================

@require_POST
def register_citizen(request):

    full_name = request.POST.get(
        "full_name",
        ""
    ).strip()

    email = request.POST.get(
        "email",
        ""
    ).strip().lower()

    phone = request.POST.get(
        "phone",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    )

    confirm_password = request.POST.get(
        "confirm_password",
        ""
    )

    security_question = request.POST.get(
        "security_question",
        ""
    ).strip()

    security_answer = request.POST.get(
        "security_answer",
        ""
    ).strip()

    # -----------------------------------------------------
    # Required fields
    # -----------------------------------------------------

    if not all([
        full_name,
        email,
        phone,
        password,
        confirm_password,
        security_question,
        security_answer
    ]):
        return JsonResponse({
            "success": False,
            "message": "Please fill all the required fields."
        }, status=400)

    # -----------------------------------------------------
    # Phone validation
    # -----------------------------------------------------

    if not phone.isdigit() or len(phone) != 10:
        return JsonResponse({
            "success": False,
            "message": "Please enter a valid 10-digit phone number."
        }, status=400)

    # -----------------------------------------------------
    # Password confirmation
    # -----------------------------------------------------

    if password != confirm_password:
        return JsonResponse({
            "success": False,
            "message": "Passwords do not match."
        }, status=400)

    # -----------------------------------------------------
    # Django password validation
    # -----------------------------------------------------

    try:
        validate_password(password)
    except ValidationError as error:
        return JsonResponse({
            "success": False,
            "message": " ".join(error.messages)
        }, status=400)

    # -----------------------------------------------------
    # Email duplicate check
    # -----------------------------------------------------

    if User.objects.filter(
        email__iexact=email
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "Email already registered."
        }, status=400)

    # -----------------------------------------------------
    # Generate username
    # -----------------------------------------------------

    username = email.split("@")[0]

    original_username = username
    counter = 1

    while User.objects.filter(
        username__iexact=username
    ).exists():

        username = f"{original_username}{counter}"
        counter += 1

    # -----------------------------------------------------
    # Create user + citizen profile
    # -----------------------------------------------------

    try:
        with transaction.atomic():

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role="citizen"
            )

            citizen_id = get_next_citizen_id()

            citizen = Citizen.objects.create(
                user=user,
                citizen_id=citizen_id,
                full_name=full_name,
                phone=phone,
                security_question=security_question,
                security_answer=make_password(
                    security_answer.lower()
                )
            )

            # Login immediately after registration
            login(request, user)

    except Exception:
        return JsonResponse({
            "success": False,
            "message": "Unable to create account. Please try again."
        }, status=500)

    return redirect("/citizen-dashboard/")


# =========================================================
# CITIZEN LOGIN PAGE
# =========================================================

def login_page(request):
    return render(request, "login.html")


# =========================================================
# CITIZEN LOGIN
# =========================================================

def citizen_login(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST method is allowed."
        }, status=405)

    login_value = request.POST.get(
        "login_value",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    )

    if not login_value or not password:
        return JsonResponse({
            "success": False,
            "message": "Please enter login details."
        }, status=400)

    user = None

    # -----------------------------------------------------
    # Login using Citizen ID
    # -----------------------------------------------------

    citizen = (
        Citizen.objects
        .select_related("user")
        .filter(
            citizen_id__iexact=login_value
        )
        .first()
    )

    if citizen:
        user = citizen.user

    # -----------------------------------------------------
    # Login using email
    # -----------------------------------------------------

    else:
        user = (
            User.objects
            .filter(
                email__iexact=login_value,
                role="citizen"
            )
            .first()
        )

    # -----------------------------------------------------
    # Password verification
    # -----------------------------------------------------

    if not user or not user.check_password(password):
        return JsonResponse({
            "success": False,
            "message": "Invalid email/citizen ID or password."
        }, status=400)

    if not user.is_active:
        return JsonResponse({
            "success": False,
            "message": "Your account is inactive."
        }, status=403)

    login(request, user)

    return redirect("/citizen-dashboard/")


# =========================================================
# CITIZEN DASHBOARD
# =========================================================

def citizen_dashboard(request):

    citizen = citizen_required(request)

    if not citizen:
        return redirect("/login/")

    complaints = (
        Complaint.objects
        .filter(citizen=citizen)
        .order_by("-created_at")
    )

    # -----------------------------------------------------
    # Dashboard counts
    # -----------------------------------------------------

    total_complaints = complaints.count()

    in_progress_count = complaints.filter(
        status="in_progress"
    ).count()

    resolved_count = complaints.filter(
        status="resolved"
    ).count()

    # -----------------------------------------------------
    # Recent complaints
    # -----------------------------------------------------

    recent_complaints = complaints[:3]

    latest_complaint = complaints.first()

    # -----------------------------------------------------
    # Initials
    # -----------------------------------------------------

    initials = get_initials(
        citizen.full_name,
        "C"
    )

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

            # Upvote system currently not implemented
            "my_upvotes": 0,
        }
    )


# =========================================================
# MY COMPLAINTS
# =========================================================

def my_complaints(request):

    citizen = citizen_required(request)

    if not citizen:
        return redirect("/login/")

    complaints = (
        Complaint.objects
        .filter(citizen=citizen)
        .order_by("-created_at")
    )

    total_complaints = complaints.count()

    reported_count = complaints.filter(
        status="reported"
    ).count()

    in_progress_count = complaints.filter(
        status="in_progress"
    ).count()

    resolved_count = complaints.filter(
        status="resolved"
    ).count()

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


# =========================================================
# OFFICER REGISTER PAGE
# =========================================================

def officer_register_page(request):
    return render(
        request,
        "officer_register.html"
    )


# =========================================================
# OFFICER REGISTER
# =========================================================

@require_POST
def officer_register(request):

    full_name = request.POST.get(
        "full_name",
        ""
    ).strip()

    employee_id = request.POST.get(
        "employee_id",
        ""
    ).strip().upper()

    email = request.POST.get(
        "email",
        ""
    ).strip().lower()

    phone = request.POST.get(
        "phone",
        ""
    ).strip()

    department = request.POST.get(
        "department",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    )

    confirm_password = request.POST.get(
        "confirm_password",
        ""
    )

    security_question = request.POST.get(
        "security_question",
        ""
    ).strip()

    security_answer = request.POST.get(
        "security_answer",
        ""
    ).strip()

    # -----------------------------------------------------
    # Required fields
    # -----------------------------------------------------

    if not all([
        full_name,
        employee_id,
        email,
        phone,
        department,
        password,
        confirm_password,
        security_question,
        security_answer
    ]):
        return JsonResponse({
            "success": False,
            "message": "All fields are required."
        }, status=400)

    # -----------------------------------------------------
    # Employee ID validation
    # -----------------------------------------------------

    if (
        not employee_id.isalnum()
        or len(employee_id) > 10
    ):
        return JsonResponse({
            "success": False,
            "message": (
                "Employee ID must contain only letters and "
                "numbers and cannot exceed 10 characters."
            )
        }, status=400)

    # -----------------------------------------------------
    # Phone validation
    # -----------------------------------------------------

    if not phone.isdigit() or len(phone) != 10:
        return JsonResponse({
            "success": False,
            "message": "Please enter a valid 10-digit phone number."
        }, status=400)

    # -----------------------------------------------------
    # Password validation
    # -----------------------------------------------------

    if password != confirm_password:
        return JsonResponse({
            "success": False,
            "message": "Passwords do not match."
        }, status=400)

    try:
        validate_password(password)
    except ValidationError as error:
        return JsonResponse({
            "success": False,
            "message": " ".join(error.messages)
        }, status=400)

    # -----------------------------------------------------
    # Duplicate Employee ID
    # -----------------------------------------------------

    if Officer.objects.filter(
        employee_id__iexact=employee_id
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "Employee ID is already registered."
        }, status=400)

    # -----------------------------------------------------
    # Duplicate email
    # -----------------------------------------------------

    if User.objects.filter(
        email__iexact=email
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "Email is already registered."
        }, status=400)

    # -----------------------------------------------------
    # Duplicate username
    # -----------------------------------------------------

    if User.objects.filter(
        username__iexact=employee_id
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "Employee ID is already in use."
        }, status=400)

    # -----------------------------------------------------
    # Create officer
    # -----------------------------------------------------

    try:
        with transaction.atomic():

            user = User.objects.create_user(
                username=employee_id,
                email=email,
                password=password,
                role="officer"
            )

            officer = Officer.objects.create(
                user=user,
                employee_id=employee_id,
                full_name=full_name,
                phone=phone,
                department=department,
                is_approved=False,
                security_question=security_question,
                security_answer=make_password(
                    security_answer.lower()
                )
            )

    except Exception:
        return JsonResponse({
            "success": False,
            "message": (
                "Unable to submit officer registration. "
                "Please try again."
            )
        }, status=500)

    return JsonResponse({
        "success": True,
        "message": (
            "Officer registration submitted. "
            "Your account is pending admin verification."
        ),
        "employee_id": officer.employee_id
    }, status=201)


# =========================================================
# OFFICER LOGIN PAGE
# =========================================================

def officer_login_page(request):
    return render(
        request,
        "officer_login.html"
    )


# =========================================================
# OFFICER LOGIN
# =========================================================

def officer_login(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Only POST method is allowed."
        }, status=405)

    employee_id = request.POST.get(
        "employee_id",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    )

    if not employee_id or not password:
        return JsonResponse({
            "success": False,
            "message": "Please enter Employee ID and Password."
        }, status=400)

    try:
        officer = (
            Officer.objects
            .select_related("user")
            .get(
                employee_id__iexact=employee_id
            )
        )

    except Officer.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Invalid Employee ID or Password."
        }, status=401)

    # -----------------------------------------------------
    # Approval check
    # -----------------------------------------------------

    if not officer.is_approved:
        return JsonResponse({
            "success": False,
            "message": (
                "Your officer account has not been approved yet."
            )
        }, status=403)

    # -----------------------------------------------------
    # Active account check
    # -----------------------------------------------------

    if not officer.user.is_active:
        return JsonResponse({
            "success": False,
            "message": "Your officer account is inactive."
        }, status=403)

    # -----------------------------------------------------
    # Authenticate
    # -----------------------------------------------------

    user = authenticate(
        request,
        username=officer.user.username,
        password=password
    )

    if user is None:
        return JsonResponse({
            "success": False,
            "message": "Invalid Employee ID or Password."
        }, status=401)

    login(request, user)

    return redirect("/officer-dashboard/")


# =========================================================
# OFFICER DASHBOARD
# =========================================================

def officer_dashboard(request):

    officer = officer_required(request)

    if not officer:
        return redirect("/officer-login/")

    complaints = (
        Complaint.objects
        .select_related(
            "citizen",
            "assigned_officer"
        )
        .filter(
            assigned_officer=officer
        )
        .order_by("-created_at")
    )

    # -----------------------------------------------------
    # Counts
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Recent complaints
    # -----------------------------------------------------

    recent_complaints = complaints[:3]

    # -----------------------------------------------------
    # Priority complaints
    # -----------------------------------------------------

    priority_complaints = (
        complaints
        .order_by(
            "-upvotes",
            "-created_at"
        )[:3]
    )

    initials = get_initials(
        officer.full_name,
        "O"
    )

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
            "assigned_complaints": complaints,
            "recent_complaints": recent_complaints,
            "priority_complaints": priority_complaints,
        }
    )


# =========================================================
# UPDATE COMPLAINT STATUS - OFFICER
# =========================================================

@require_POST
def update_complaint_status(
    request,
    complaint_id
):

    officer = officer_required(request)

    if not officer:
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

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

    status_value = (
        request.POST.get(
            "status",
            ""
        )
        .strip()
    )

    allowed_statuses = {
        "reported",
        "in_progress",
        "resolved"
    }

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


# =========================================================
# OFFICER COMPLAINTS
# =========================================================

def officer_complaints(request):

    officer = officer_required(request)

    if not officer:
        return redirect("/officer-login/")

    complaints = (
        Complaint.objects
        .select_related(
            "citizen",
            "assigned_officer"
        )
        .filter(
            assigned_officer=officer
        )
        .order_by("-created_at")
    )

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

    initials = get_initials(
        officer.full_name,
        "O"
    )

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


# =========================================================
# OFFICER COMPLAINT DETAILS
# =========================================================

def officer_complaint_details(
    request,
    complaint_id
):

    officer = officer_required(request)

    if not officer:
        return redirect("/officer-login/")

    complaint = (
        Complaint.objects
        .select_related(
            "citizen",
            "assigned_officer"
        )
        .filter(
            id=complaint_id,
            assigned_officer=officer
        )
        .first()
    )

    if not complaint:
        return redirect("/officer-complaints/")

    return render(
        request,
        "officer_complaint_details.html",
        {
            "officer": officer,
            "complaint": complaint,
        }
    )
@login_required
def verify_complaint(request, complaint_id):

    if request.method != "POST":
        return redirect("officer_complaints")

    complaint = get_object_or_404(
        Complaint,
        id=complaint_id
    )

    # Only officer can verify
    if request.user.role != "officer":
        return redirect("home")

    officer = getattr(
        request.user,
        "officer_profile",
        None
    )

    if officer is None:
        return redirect("officer_login")

    # Only assigned officer can verify
    if complaint.assigned_officer != officer:
        return redirect("officer_complaints")

    # Verify complaint
    complaint.is_verified = True

    # Once verified, priority becomes LOW
    complaint.priority = "low"

    # Keep complaint reported until officer starts work
    complaint.status = "reported"
    complaint.progress = 0

    complaint.save()

    return redirect(
        "officer_complaint_details",
        complaint_id=complaint.id
    )

# =========================================================
# OFFICER LOGOUT
# =========================================================

def officer_logout(request):

    logout(request)

    return redirect("/officer-login/")


# =========================================================
# CITIZEN LOGOUT
# =========================================================

def citizen_logout(request):

    logout(request)

    return redirect("/login/")


# =========================================================
# REPORT ISSUE
# =========================================================

def report_issue(request):

    citizen = citizen_required(request)

    if not citizen:
        return redirect("/login/")

    initials = get_initials(
        citizen.full_name,
        "C"
    )

    return render(
        request,
        "report_issue.html",
        {
            "citizen": citizen,
            "initials": initials,
        }
    )


# =========================================================
# SUBMIT COMPLAINT
# =========================================================

@require_POST
def submit_complaint(request):

    citizen = citizen_required(request)

    if not citizen:
        return JsonResponse({
            "success": False,
            "message": "Authentication required."
        }, status=401)

    category = request.POST.get(
        "category",
        ""
    ).strip()

    title = request.POST.get(
        "issue_title",
        ""
    ).strip()

    description = request.POST.get(
        "description",
        ""
    ).strip()

    address = request.POST.get(
        "location",
        ""
    ).strip()

    latitude = request.POST.get(
        "latitude",
        ""
    ).strip()

    longitude = request.POST.get(
        "longitude",
        ""
    ).strip()

    photo = request.FILES.get(
        "issue_photo"
    )

    # -----------------------------------------------------
    # Required fields
    # -----------------------------------------------------

    if not all([
        category,
        title,
        description,
        address
    ]):
        return JsonResponse({
            "success": False,
            "message": "Please fill all required fields."
        }, status=400)

    # -----------------------------------------------------
    # Image validation
    # -----------------------------------------------------

    is_valid, image_error = validate_uploaded_image(
        photo
    )

    if not is_valid:
        return JsonResponse({
            "success": False,
            "message": image_error
        }, status=400)

    # -----------------------------------------------------
    # Create complaint
    # -----------------------------------------------------

    try:
        with transaction.atomic():

            complaint_id = get_next_complaint_id()

            complaint = Complaint.objects.create(
                complaint_id=complaint_id,
                citizen=citizen,
                category=category,
                title=title,
                description=description,
                photo=photo,
                address=address,
                latitude=latitude or None,
                longitude=longitude or None,
                status="reported"
            )

    except Exception:
        return JsonResponse({
            "success": False,
            "message": (
                "Unable to submit complaint. "
                "Please try again."
            )
        }, status=500)

    messages.success(
        request,
        (
            "Your complaint has been successfully submitted. "
            f"Complaint ID: {complaint.complaint_id}"
        )
    )

    return redirect("citizen_dashboard")


# =========================================================
# ADMIN LOGIN PAGE
# =========================================================

def admin_login_page(request):
    return render(
        request,
        "admin_login.html"
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@require_POST
def admin_login(request):

    admin_id = request.POST.get(
        "admin_id",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    )

    if not admin_id or not password:
        return render(
            request,
            "admin_login.html",
            {
                "error": (
                    "Please enter Admin ID and password."
                )
            }
        )

    try:
        user = User.objects.get(
            username=admin_id
        )

    except User.DoesNotExist:
        return render(
            request,
            "admin_login.html",
            {
                "error": "Invalid Admin ID or password."
            }
        )

    if user.role != "admin":
        return render(
            request,
            "admin_login.html",
            {
                "error": (
                    "You are not authorized as an admin."
                )
            }
        )

    if not user.is_active:
        return render(
            request,
            "admin_login.html",
            {
                "error": "Your admin account is inactive."
            }
        )

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

    login(
        request,
        authenticated_user
    )

    return redirect("/admin-dashboard/")


# =========================================================
# ADMIN OFFICER VERIFICATION
# =========================================================

def admin_officer_verification(request):

    if not admin_required(request):
        return redirect("/admin-login/")

    pending_officers = (
        Officer.objects
        .filter(is_approved=False)
        .select_related("user")
        .order_by("-created_at")
    )

    pending_officer_data = []

    for officer in pending_officers:

        pending_officer_data.append({
            "id": officer.id,
            "initials": get_initials(
                officer.full_name,
                "?"
            ),
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

    admin_initials = get_initials(
        admin_name,
        "A"
    )

    return render(
        request,
        "admin_officer_verification.html",
        {
            "pending_officers": pending_officer_data,
            "pending_count": len(
                pending_officer_data
            ),
            "admin_name": admin_name,
            "admin_initials": admin_initials,
        }
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def admin_dashboard(request):

    if not admin_required(request):
        return redirect("/admin-login/")

    admin_name = (
        request.user.get_full_name()
        or request.user.username
    )

    admin_initials = get_initials(
        admin_name,
        "A"
    )

    # -----------------------------------------------------
    # Officer data
    # -----------------------------------------------------

    pending_officer_requests = (
        Officer.objects
        .select_related("user")
        .filter(is_approved=False)
        .order_by("-created_at")
    )

    pending_requests_count = (
        pending_officer_requests.count()
    )

    approved_officers = (
        Officer.objects
        .select_related("user")
        .filter(is_approved=True)
        .order_by("full_name")
    )

    approved_officers_count = (
        approved_officers.count()
    )

    # -----------------------------------------------------
    # Department statistics
    # -----------------------------------------------------

    department_stats = []

    for (
        department_code,
        department_name
    ) in Officer.DEPARTMENT_CHOICES:

        count = Officer.objects.filter(
            department=department_code,
            is_approved=True
        ).count()

        department_stats.append({
            "name": department_name,
            "code": department_code,
            "count": count
        })

    # -----------------------------------------------------
    # Complaint statistics
    # -----------------------------------------------------

    total_complaints_count = (
        Complaint.objects.count()
    )

    reported_count = Complaint.objects.filter(
        status="reported"
    ).count()

    in_progress_count = Complaint.objects.filter(
        status="in_progress"
    ).count()

    resolved_count = Complaint.objects.filter(
        status="resolved"
    ).count()

    unassigned_count = Complaint.objects.filter(
        assigned_officer__isnull=True
    ).count()

    # -----------------------------------------------------
    # Unassigned complaints
    # -----------------------------------------------------

    unassigned_complaints = (
        Complaint.objects
        .select_related("citizen")
        .filter(
            assigned_officer__isnull=True
        )
        .order_by("-created_at")
    )

    # -----------------------------------------------------
    # Assigned complaints
    # -----------------------------------------------------

    assigned_complaints = (
        Complaint.objects
        .select_related(
            "citizen",
            "assigned_officer"
        )
        .filter(
            assigned_officer__isnull=False
        )
        .order_by("-updated_at")
    )

    # -----------------------------------------------------
    # Assignment data
    # -----------------------------------------------------

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
            "created_at": complaint.created_at.strftime(
                "%d %b %Y, %I:%M %p"
            ),
        })

    # -----------------------------------------------------
    # Citizens
    # -----------------------------------------------------

    citizens = (
        Citizen.objects
        .select_related("user")
        .prefetch_related("complaints")
        .order_by("-id")
    )

    citizen_list = []

    for citizen in citizens:

        complaints = list(
            citizen.complaints.all()
        )

        categories = []

        for complaint in complaints:

            category_name = (
                complaint.get_category_display()
            )

            if category_name not in categories:
                categories.append(
                    category_name
                )

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

    total_citizens_count = len(
        citizen_list
    )

    # -----------------------------------------------------
    # Recent complaints
    # -----------------------------------------------------

    recent_complaints = (
        Complaint.objects
        .select_related(
            "citizen",
            "assigned_officer"
        )
        .order_by("-created_at")[:10]
    )

    # -----------------------------------------------------
    # Recent activity
    # -----------------------------------------------------

    recent_activity = []

    for complaint in recent_complaints:

        recent_activity.append({
            "type": "complaint",
            "title": (
                "New complaint reported by "
                f"{complaint.citizen.full_name}"
            ),
            "description": complaint.title,
            "complaint_id": complaint.complaint_id,
            "status": complaint.get_status_display(),
            "created_at": complaint.created_at,
        })

    # -----------------------------------------------------
    # Context
    # -----------------------------------------------------

    context = {
        "admin_name": admin_name,
        "admin_initials": admin_initials,

        "pending_requests_count":
            pending_requests_count,

        "approved_officers_count":
            approved_officers_count,

        "pending_officer_requests":
            pending_officer_requests,

        "approved_officers":
            approved_officers,

        "department_stats":
            department_stats,

        "total_complaints_count":
            total_complaints_count,

        "reported_count":
            reported_count,

        "in_progress_count":
            in_progress_count,

        "resolved_count":
            resolved_count,

        "unassigned_count":
            unassigned_count,

        "unassigned_complaints":
            unassigned_complaints,

        "assigned_complaints":
            assigned_complaints,

        "assignment_complaints_data":
            assignment_complaints_data,

        "recent_complaints":
            recent_complaints,

        "citizens":
            citizen_list,

        "total_citizens_count":
            total_citizens_count,

        "recent_activity":
            recent_activity,
    }

    return render(
        request,
        "admin_dashboard.html",
        context
    )


# =========================================================
# ADMIN CATEGORY VIEW
# =========================================================

def admin_category_view(
    request,
    department_code
):

    if not admin_required(request):
        return redirect("/admin-login/")

    department_dict = dict(
        Officer.DEPARTMENT_CHOICES
    )

    if department_code not in department_dict:
        return redirect("/admin-dashboard/")

    department_name = (
        department_dict[department_code]
    )

    # -----------------------------------------------------
    # Approved officers
    # -----------------------------------------------------

    officers = (
        Officer.objects
        .select_related("user")
        .filter(
            department=department_code,
            is_approved=True
        )
        .order_by("full_name")
    )

    # -----------------------------------------------------
    # Categories for department
    # -----------------------------------------------------

    complaint_categories = [
        category_code
        for category_code, department
        in CATEGORY_DEPARTMENT_MAP.items()
        if department == department_code
    ]

    # -----------------------------------------------------
    # Unassigned complaints
    # -----------------------------------------------------

    complaints = (
        Complaint.objects
        .select_related(
            "citizen",
            "assigned_officer"
        )
        .filter(
            category__in=complaint_categories,
            assigned_officer__isnull=True
        )
        .order_by("-created_at")
    )

    # -----------------------------------------------------
    # Assigned complaints
    # -----------------------------------------------------

    assigned_complaints = (
        Complaint.objects
        .select_related(
            "citizen",
            "assigned_officer"
        )
        .filter(
            category__in=complaint_categories,
            assigned_officer__isnull=False
        )
        .order_by("-updated_at")
    )

    context = {
        "department_code":
            department_code,

        "department_name":
            department_name,

        "officers":
            officers,

        "officer_count":
            officers.count(),

        "complaints":
            complaints,

        "complaint_count":
            complaints.count(),

        "assigned_complaints":
            assigned_complaints,
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
def assign_complaint(
    request,
    complaint_id
):

    if not admin_required(request):
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    officer_id = request.POST.get(
        "officer_id",
        ""
    ).strip()

    if not officer_id:
        return JsonResponse({
            "success": False,
            "message": "Please select an officer."
        }, status=400)

    # -----------------------------------------------------
    # Get complaint
    # -----------------------------------------------------

    complaint = (
        Complaint.objects
        .select_related("citizen")
        .filter(id=complaint_id)
        .first()
    )

    if not complaint:
        return JsonResponse({
            "success": False,
            "message": "Complaint not found."
        }, status=404)

    # -----------------------------------------------------
    # Get approved officer
    # -----------------------------------------------------

    officer = (
        Officer.objects
        .filter(
            id=officer_id,
            is_approved=True
        )
        .first()
    )

    if not officer:
        return JsonResponse({
            "success": False,
            "message": "Approved officer not found."
        }, status=404)

    # -----------------------------------------------------
    # Department validation
    # -----------------------------------------------------

    required_department = (
        CATEGORY_DEPARTMENT_MAP.get(
            complaint.category
        )
    )

    if (
        required_department
        and required_department != officer.department
    ):
        return JsonResponse({
            "success": False,
            "message": (
                "This officer does not belong to "
                "the required department."
            )
        }, status=400)

    # -----------------------------------------------------
    # Assign complaint
    # -----------------------------------------------------

    complaint.assigned_officer = officer

    # Automatically move reported complaint
    # into in-progress state.
    if complaint.status == "reported":
        complaint.status = "in_progress"

    complaint.save(
        update_fields=[
            "assigned_officer",
            "status",
            "updated_at"
        ]
    )

    return JsonResponse({
        "success": True,
        "message": "Complaint assigned successfully.",
        "complaint_id": complaint.complaint_id,
        "officer_name": officer.full_name,
        "citizen_name": complaint.citizen.full_name,
        "status": complaint.get_status_display(),
    })


# =========================================================
# ADMIN - APPROVE OFFICER
# =========================================================

@require_POST
def approve_officer(
    request,
    officer_id
):

    if not admin_required(request):
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    officer = (
        Officer.objects
        .filter(id=officer_id)
        .first()
    )

    if not officer:
        return JsonResponse({
            "success": False,
            "message": "Officer not found."
        }, status=404)

    if officer.is_approved:
        return JsonResponse({
            "success": False,
            "message": "Officer is already approved."
        }, status=400)

    officer.is_approved = True

    officer.save(
        update_fields=[
            "is_approved"
        ]
    )

    return JsonResponse({
        "success": True,
        "message": "Officer approved successfully."
    })


# =========================================================
# ADMIN - REJECT OFFICER
# =========================================================

@require_POST
def reject_officer(
    request,
    officer_id
):

    if not admin_required(request):
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    officer = (
        Officer.objects
        .select_related("user")
        .filter(id=officer_id)
        .first()
    )

    if not officer:
        return JsonResponse({
            "success": False,
            "message": "Officer not found."
        }, status=404)

    user = officer.user

    try:
        with transaction.atomic():
            officer.delete()
            user.delete()

    except Exception:
        return JsonResponse({
            "success": False,
            "message": (
                "Unable to reject officer registration."
            )
        }, status=500)

    return JsonResponse({
        "success": True,
        "message": "Officer registration rejected."
    })


# =========================================================
# ADMIN LOGOUT
# =========================================================

def admin_logout(request):

    logout(request)

    return redirect("/admin-login/")


# =========================================================
# UPDATE COMPLAINT PROGRESS
# =========================================================

@require_POST
def update_complaint_progress(
    request,
    complaint_id
):

    officer = officer_required(request)

    if not officer:
        return JsonResponse({
            "success": False,
            "message": "Unauthorized access."
        }, status=403)

    complaint = (
        Complaint.objects
        .filter(
            id=complaint_id,
            assigned_officer=officer
        )
        .first()
    )

    if not complaint:
        return JsonResponse({
            "success": False,
            "message": "Complaint is not assigned to you."
        }, status=404)

    progress_value = request.POST.get(
        "progress",
        ""
    ).strip()

    try:
        progress = int(progress_value)

    except (TypeError, ValueError):
        return JsonResponse({
            "success": False,
            "message": "Progress must be a valid number."
        }, status=400)

    # -----------------------------------------------------
    # Progress range
    # -----------------------------------------------------

    if progress < 0 or progress > 100:
        return JsonResponse({
            "success": False,
            "message": "Progress must be between 0 and 100."
        }, status=400)

    complaint.progress = progress

    # Optional logical status update
    if progress == 100:
        complaint.status = "resolved"

    elif progress > 0 and complaint.status == "reported":
        complaint.status = "in_progress"

    complaint.save(
        update_fields=[
            "progress",
            "status",
            "updated_at"
        ]
    )

    return JsonResponse({
        "success": True,
        "message": "Complaint progress updated successfully.",
        "progress": progress,
        "status": complaint.get_status_display()
    })


# =========================================================
# FORGOT PASSWORD PAGE
# =========================================================

def forgot_password_page(request):

    role = request.GET.get(
        "role",
        "citizen"
    ).lower()

    if role not in {
        "citizen",
        "officer"
    }:
        role = "citizen"

    return render(
        request,
        "forgot_password.html",
        {
            "role": role
        }
    )


# =========================================================
# FORGOT PASSWORD - FIND ACCOUNT
# =========================================================

@require_POST
def forgot_password_start(request):

    role = request.POST.get(
        "role",
        "citizen"
    ).lower()

    identifier = request.POST.get(
        "identifier",
        ""
    ).strip()

    if role not in {
        "citizen",
        "officer"
    }:
        return render(
            request,
            "forgot_password.html",
            {
                "role": "citizen",
                "error": "Invalid account type."
            }
        )

    if not identifier:
        return render(
            request,
            "forgot_password.html",
            {
                "role": role,
                "error": (
                    "Please enter your account ID or email."
                )
            }
        )

    # -----------------------------------------------------
    # Find profile
    # -----------------------------------------------------

    profile = None

    if role == "citizen":

        profile = (
            Citizen.objects
            .select_related("user")
            .filter(
                user__role="citizen"
            )
            .filter(
                Q(
                    citizen_id__iexact=identifier
                )
                |
                Q(
                    user__email__iexact=identifier
                )
            )
            .first()
        )

    else:

        profile = (
            Officer.objects
            .select_related("user")
            .filter(
                user__role="officer"
            )
            .filter(
                Q(
                    employee_id__iexact=identifier
                )
                |
                Q(
                    user__email__iexact=identifier
                )
            )
            .first()
        )

    if not profile:
        return render(
            request,
            "forgot_password.html",
            {
                "role": role,
                "error": (
                    "Account not found. "
                    "Please check your details."
                )
            }
        )

    # -----------------------------------------------------
    # Security question check
    # -----------------------------------------------------

    if (
        not profile.security_question
        or not profile.security_answer
    ):
        return render(
            request,
            "forgot_password.html",
            {
                "role": role,
                "error": (
                    "Security question is not configured "
                    "for this account. Please contact "
                    "the administrator."
                )
            }
        )

    # -----------------------------------------------------
    # Store reset session
    # -----------------------------------------------------

    request.session[
        "forgot_reset_profile_id"
    ] = profile.id

    request.session[
        "forgot_reset_role"
    ] = role

    request.session[
        "forgot_reset_attempts"
    ] = 0

    request.session[
        "forgot_reset_verified"
    ] = False

    # -----------------------------------------------------
    # Get security question text
    # -----------------------------------------------------

    question_dict = dict(
        Citizen.SECURITY_QUESTION_CHOICES
    )

    question_text = question_dict.get(
        profile.security_question,
        profile.security_question
    )

    return render(
        request,
        "forgot_password_question.html",
        {
            "role": role,
            "question": question_text
        }
    )


# =========================================================
# FORGOT PASSWORD - VERIFY SECURITY ANSWER
# =========================================================

@require_POST
def forgot_password_verify(request):

    role = request.session.get(
        "forgot_reset_role"
    )

    profile_id = request.session.get(
        "forgot_reset_profile_id"
    )

    if not role or not profile_id:
        return redirect(
            f"/forgot-password/?role={role or 'citizen'}"
        )

    attempts = request.session.get(
        "forgot_reset_attempts",
        0
    )

    # -----------------------------------------------------
    # Maximum attempts
    # -----------------------------------------------------

    if attempts >= 3:

        request.session.pop(
            "forgot_reset_profile_id",
            None
        )

        request.session.pop(
            "forgot_reset_role",
            None
        )

        request.session.pop(
            "forgot_reset_attempts",
            None
        )

        request.session.pop(
            "forgot_reset_verified",
            None
        )

        return render(
            request,
            "forgot_password.html",
            {
                "role": role,
                "error": (
                    "Too many incorrect attempts. "
                    "Please start the password reset process again."
                )
            }
        )

    answer = request.POST.get(
        "security_answer",
        ""
    ).strip().lower()

    # -----------------------------------------------------
    # Get profile
    # -----------------------------------------------------

    if role == "citizen":

        profile = (
            Citizen.objects
            .select_related("user")
            .filter(id=profile_id)
            .first()
        )

    else:

        profile = (
            Officer.objects
            .select_related("user")
            .filter(id=profile_id)
            .first()
        )

    if not profile:

        request.session.flush()

        return redirect(
            "/forgot-password/"
        )

    # -----------------------------------------------------
    # Verify hashed answer
    # -----------------------------------------------------

    if not check_password(
        answer,
        profile.security_answer
    ):

        attempts += 1

        request.session[
            "forgot_reset_attempts"
        ] = attempts

        remaining = 3 - attempts

        if remaining <= 0:

            request.session.pop(
                "forgot_reset_profile_id",
                None
            )

            request.session.pop(
                "forgot_reset_role",
                None
            )

            request.session.pop(
                "forgot_reset_attempts",
                None
            )

            request.session.pop(
                "forgot_reset_verified",
                None
            )

            return render(
                request,
                "forgot_password.html",
                {
                    "role": role,
                    "error": (
                        "Too many incorrect attempts. "
                        "Please start again."
                    )
                }
            )

        question_dict = dict(
            Citizen.SECURITY_QUESTION_CHOICES
        )

        return render(
            request,
            "forgot_password_question.html",
            {
                "role": role,
                "question": question_dict.get(
                    profile.security_question,
                    profile.security_question
                ),
                "error": (
                    "Incorrect answer. "
                    f"{remaining} attempt(s) remaining."
                )
            }
        )

    # -----------------------------------------------------
    # Correct answer
    # -----------------------------------------------------

    request.session[
        "forgot_reset_verified"
    ] = True

    return render(
        request,
        "forgot_password_reset.html",
        {
            "role": role
        }
    )


# =========================================================
# FORGOT PASSWORD - SET NEW PASSWORD
# =========================================================

@require_POST
def forgot_password_reset(request):

    role = request.session.get(
        "forgot_reset_role"
    )

    profile_id = request.session.get(
        "forgot_reset_profile_id"
    )

    verified = request.session.get(
        "forgot_reset_verified",
        False
    )

    if (
        not role
        or not profile_id
        or not verified
    ):
        return redirect(
            f"/forgot-password/?role={role or 'citizen'}"
        )

    new_password = request.POST.get(
        "new_password",
        ""
    )

    confirm_password = request.POST.get(
        "confirm_password",
        ""
    )

    # -----------------------------------------------------
    # Required fields
    # -----------------------------------------------------

    if not new_password or not confirm_password:
        return render(
            request,
            "forgot_password_reset.html",
            {
                "role": role,
                "error": "All fields are required."
            }
        )

    # -----------------------------------------------------
    # Password confirmation
    # -----------------------------------------------------

    if new_password != confirm_password:
        return render(
            request,
            "forgot_password_reset.html",
            {
                "role": role,
                "error": "Passwords do not match."
            }
        )

    # -----------------------------------------------------
    # Minimum length
    # -----------------------------------------------------

    if len(new_password) < 8:
        return render(
            request,
            "forgot_password_reset.html",
            {
                "role": role,
                "error": (
                    "Password must contain at least 8 characters."
                )
            }
        )

    # -----------------------------------------------------
    # Get profile
    # -----------------------------------------------------

    if role == "citizen":

        profile = (
            Citizen.objects
            .select_related("user")
            .filter(id=profile_id)
            .first()
        )

    else:

        profile = (
            Officer.objects
            .select_related("user")
            .filter(id=profile_id)
            .first()
        )

    if not profile:

        request.session.flush()

        return redirect(
            "/forgot-password/"
        )

    user = profile.user

    # -----------------------------------------------------
    # Django password validation
    # -----------------------------------------------------

    try:

        validate_password(
            new_password,
            user
        )

    except ValidationError as error:

        return render(
            request,
            "forgot_password_reset.html",
            {
                "role": role,
                "error": " ".join(
                    error.messages
                )
            }
        )

    # -----------------------------------------------------
    # Set new password
    # -----------------------------------------------------

    user.set_password(
        new_password
    )

    user.save(
        update_fields=[
            "password"
        ]
    )

    # -----------------------------------------------------
    # Clear reset session
    # -----------------------------------------------------

    request.session.pop(
        "forgot_reset_profile_id",
        None
    )

    request.session.pop(
        "forgot_reset_role",
        None
    )

    request.session.pop(
        "forgot_reset_attempts",
        None
    )

    request.session.pop(
        "forgot_reset_verified",
        None
    )

    return render(
        request,
        "forgot_password_complete.html",
        {
            "role": role
        }
    )