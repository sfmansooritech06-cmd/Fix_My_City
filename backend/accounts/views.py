from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password

from .models import User, Citizen
from django.shortcuts import render


def home(request):
    return render(request, "index.html")

@csrf_exempt
def register_citizen(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Only POST method is allowed."
            },
            status=405
        )

    full_name = request.POST.get("full_name", "").strip()
    email = request.POST.get("email", "").strip().lower()
    phone = request.POST.get("phone", "").strip()
    password = request.POST.get("password", "")
    confirm_password = request.POST.get("confirm_password", "")

    # Check empty fields
    if not full_name or not email or not phone or not password:
        return JsonResponse(
            {
                "success": False,
                "message": "All fields are required."
            },
            status=400
        )

    # Check password
    if password != confirm_password:
        return JsonResponse(
            {
                "success": False,
                "message": "Passwords do not match."
            },
            status=400
        )

    # Check existing email
    if User.objects.filter(email=email).exists():
        return JsonResponse(
            {
                "success": False,
                "message": "Email already registered."
            },
            status=400
        )

    # Generate username internally
    username = email.split("@")[0]

    # Make username unique
    original_username = username
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{original_username}{counter}"
        counter += 1

    # Create User
    user = User.objects.create(
        username=username,
        email=email,
        password=make_password(password),
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

    return JsonResponse(
        {
            "success": True,
            "message": "Account created successfully.",
            "citizen_id": citizen.citizen_id
        },
        status=201
    )