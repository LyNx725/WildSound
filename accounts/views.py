from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.http import HttpResponse

User = get_user_model()  # ✅ Get the correct custom user model

def home(request):
    return HttpResponse("Welcome to the Wildlife Monitoring System!")


@api_view(["POST"])
def register_user(request):
    """API for user registration."""
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password or not username:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    user.save()

    return Response({"message": "User registered successfully", "email": user.email}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def login_user(request):
    """API for user login."""
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        user = User.objects.get(email=email)  # ✅ Get user by email
        user = authenticate(request, username=user.username, password=password)  # Authenticate using username

        if user:
            login(request, user)
            return Response({"message": "Login successful", "email": user.email}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
