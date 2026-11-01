from django.shortcuts import render

def home(request):
    return render(request, "core_templates/home.html")

def about(request):
    return render(request, "core_templates/about.html")

def custom_404(request, exception):
    return render(request, "404.html", status=404)