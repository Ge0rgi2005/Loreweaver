from django.shortcuts import render

def home(request):
    return render(request, "core/home.html")

def about(request):
    return render(request, "core/about.html")

def custom_404(request, exception):
    return render(request, "core/404.html", status=404)