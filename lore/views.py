from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .forms import LoreEntryForm
from .models import LoreEntry

def lore_entry_list(request):
    entries = LoreEntry.objects.all()
    return render(request, "lore_templates/lore_list.html", {"entries": entries})

def lore_entry_detail(request, pk):
    entry = get_object_or_404(LoreEntry, pk=pk)
    return render(request, "lore_templates/lore_details.html", {"entry": entry})

def create_lore_entry(request):
    if request.method == "POST":
        form = LoreEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lore entry created successfully.")
            return redirect("lore:list")
    else:
        form = LoreEntryForm()
    return render(request, "lore_templates/lore_form.html", {"form": form, "page_title": "Add lore entry"})

def edit_lore_entry(request, pk):
    entry = get_object_or_404(LoreEntry, pk=pk)
    if request.method == "POST":
        form = LoreEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Lore entry updated successfully.")
            return redirect("lore:detail", pk=entry.pk)
    else:
        form = LoreEntryForm(instance=entry)
    return render(
        request,
        "lore_templates/lore_form.html",
        {"form": form, "entry": entry, "page_title": "Edit lore entry"},
    )

def delete_lore_entry(request, pk):
    entry = get_object_or_404(LoreEntry, pk=pk)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Lore entry deleted successfully.")
        return redirect("lore:list")
    return render(request, "lore_templates/lore_confirm_delete.html", {"entry": entry})