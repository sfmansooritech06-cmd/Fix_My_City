from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST

from .models import User, Citizen,Complaint

import os
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# =========================
# LANDING PAGE
# =========================

def home(request):
    return render(request, "index.html")


# =========================
# CITIZEN REGISTER PAGE
# =========================

def register_page(request):
    return render(request, "register.html")


# =========================
# CITIZEN REGISTER
# =========================

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

    return JsonResponse({
        "success": True,
        "message": "Account created successfully.",
        "citizen_id": citizen.citizen_id
    }, status=201)


# =========================
# CITIZEN LOGIN PAGE
# =========================

def login_page(request):
    return render(request, "login.html")


# =========================
# CITIZEN LOGIN
# =========================

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

        return JsonResponse({
            "success": True,
            "message": "Login successful.",
            "redirect": "/citizen-dashboard/"
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid email/citizen ID or password."
    }, status=401)


# =========================
# CITIZEN DASHBOARD
# =========================
def citizen_dashboard(request):

    if not request.user.is_authenticated:
        return redirect("/login/")

    if request.user.role != "citizen":
        return redirect("/login/")

    citizen = request.user.citizen_profile

    # All complaints of logged-in citizen
    complaints = Complaint.objects.filter(
        citizen=citizen
    ).order_by("-created_at")

    # Dashboard counts
    total_complaints = complaints.count()

    in_progress_count = complaints.filter(
        status="in_progress"
    ).count()

    resolved_count = complaints.filter(
        status="resolved"
    ).count()

    # Latest 3 complaints
    recent_complaints = complaints[:3]

    # Latest complaint for status tracking
    latest_complaint = complaints.first()

    # Generate initials
    name_parts = citizen.full_name.strip().split()

    if len(name_parts) >= 2:
        initials = name_parts[0][0] + name_parts[1][0]
    else:
        initials = name_parts[0][0]

    return render(
        request,
        "citizen_dashboard.html",
        {
            "citizen": citizen,
            "initials": initials.upper(),

            "total_complaints": total_complaints,
            "in_progress_count": in_progress_count,
            "resolved_count": resolved_count,

            "recent_complaints": recent_complaints,
            "latest_complaint": latest_complaint,

            # Upvote system abhi implement nahi hua hai
            "my_upvotes": 0,
        }
    )
# =========================
# MY COMPLAINTS
# =========================

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
# =========================
# LOGOUT
# =========================

def citizen_logout(request):

    logout(request)

    return redirect("/login/")

# Report Issue

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

# Submit Complaints

# Submit Complaints

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
    # PHOTO VALIDATION (technical only — no AI/CV checks)
    # -----------------------------------------------------

    # 1. Required
    if not photo:
        return JsonResponse({
            "success": False,
            "message": "Please upload a photo of the issue."
        }, status=400)

    # 2. Extension check
    extension = os.path.splitext(photo.name)[1].lower().lstrip(".")

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return JsonResponse({
            "success": False,
            "message": "Only JPG, JPEG or PNG image files are allowed."
        }, status=400)

    # 3. Size check (5 MB max)
    if photo.size > MAX_IMAGE_SIZE_BYTES:
        return JsonResponse({
            "success": False,
            "message": "Image size must not exceed 5 MB."
        }, status=400)

    # 4. Actual image integrity check via Pillow
    #    (catches corrupted files and fake files with a spoofed extension)
    try:
        img = Image.open(photo)
        img.verify()
    except (UnidentifiedImageError, IOError, SyntaxError):
        return JsonResponse({
            "success": False,
            "message": "The uploaded file is not a valid image or is corrupted."
        }, status=400)

    # verify() consumes the file pointer — reset before any further use
    photo.seek(0)

    # 5. Confirm the actual image format matches an allowed type
    #    (protects against a .jpg extension wrapping e.g. a GIF/BMP)
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

    # Reset again before Django saves it via ImageField
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

    complaint_id = f"FMC-{next_number:06d}"

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

    return JsonResponse({
        "success": True,
        "message": "Complaint submitted successfully.",
        "complaint_id": complaint.complaint_id
    })