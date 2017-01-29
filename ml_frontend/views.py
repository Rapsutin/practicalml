from django.shortcuts import render

def index(request):
    return render(request, "ml_frontend/index.html")
