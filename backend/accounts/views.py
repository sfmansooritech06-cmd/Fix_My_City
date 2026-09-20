from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST

from .models import User, Citizen, Complaint, Officer


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

    return JsonResponse({
        "success": True,
        "message": "Account created successfully.",
        "citizen_id": citizen.citizen_id
    }, status=201)


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

        return JsonResponse({
            "success": True,
            "message": "Login successful.",
            "redirect": "/citizen-dashboard/"
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid email/citizen ID or password."
    }, status=401)


# =====================================================
# CITIZEN DASHBOARD
# =====================================================

def citizen_dashboard(request):

    if not request.user.is_authenticated:
        return redirect("/login/")

    if request.user.role != "citizen":
        return redirect("/login/")

    citizen = request.user.citizen_profile

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
        }
    )


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

    # Required fields
    if not category or not title or not description or not address:
        return JsonResponse({
            "success": False,
            "message": "Please fill all required fields."
        }, status=400)

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
    employee_id = request.POST.get(
        "employee_id",
        ""
    ).strip()

    password = request.POST.get(
        "password",
        ""
    )

    # Check empty fields
    if not employee_id or not password:
        return JsonResponse({
            "success": False,
            "message": "Please enter Employee ID and Password."
        }, status=400)

    # Find officer using Employee ID
    try:

        officer = Officer.objects.select_related(
            "user"
        ).get(
            employee_id__iexact=employee_id
        )

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

    return JsonResponse({
        "success": True,
        "message": "Officer login successful.",
        "redirect": "/officer-dashboard/"
    })


# =====================================================
# OFFICER DASHBOARD
# =====================================================

def officer_dashboard(request):

    # User must be logged in
    if not request.user.is_authenticated:
        return redirect("/officer/login/")

    # Only officers can access this dashboard
    if request.user.role != "officer":
        return redirect("/officer/login/")

    # Get Officer profile
    try:

        officer = request.user.officer_profile

    except Officer.DoesNotExist:

        logout(request)

        return redirect("/officer/login/")

    # Officer must be approved
    if not officer.is_approved:

        logout(request)

        return redirect("/officer/login/")

    # Generate initials
    name_parts = officer.full_name.strip().split()

    if len(name_parts) >= 2:
        initials = (
            name_parts[0][0] +
            name_parts[1][0]
        )
    else:
        initials = name_parts[0][0]

    return render(
        request,
        "officer_dashboard.html",
        {
            "officer": officer,
            "initials": initials.upper(),
        }
    )


# =====================================================
# OFFICER LOGOUT
# =====================================================

def officer_logout(request):

    logout(request)

    return redirect("/officer/login/")

