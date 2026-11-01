from django.contrib import messages
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from .forms import StoryEditForm, StoryForm, SceneForm, ChoiceForm, StoryFilterForm
from .models import Story, Scene, Choice

# Story Views
class StoryListView(ListView):
    model = Story
    template_name = 'story_templates/story_list.html'
    context_object_name = 'stories'
    paginate_by = 10

    def get_queryset(self):
        filter_form = StoryFilterForm(self.request.GET)
        queryset = super().get_queryset().annotate(scene_count=Count('scenes'))
        filter_form.is_valid()
        title = filter_form.cleaned_data.get('story_title')
        genre = filter_form.cleaned_data.get('story_genre')
        status = filter_form.cleaned_data.get('story_status')
        author = filter_form.cleaned_data.get('story_author')
        if title:
            queryset = queryset.filter(story_title__icontains=title)
        if genre:
            queryset = queryset.filter(story_genre=genre)
        if status:
            queryset = queryset.filter(story_status=status)
        if author:
            queryset = queryset.filter(story_author__icontains=author)

        sort_options = {
            'title': 'story_title',
            'newest': '-pk',
            'oldest': 'pk',
        }
        sort_by = filter_form.cleaned_data.get('sort_by')
        if sort_by in sort_options:
            queryset = queryset.order_by(sort_options[sort_by])
        else:
            queryset = queryset.order_by('story_title')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = StoryFilterForm(self.request.GET)
        return context

class StoryDetailView(DetailView):
    model = Story
    template_name = 'story_templates/story_details.html'
    context_object_name = 'story'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('scenes', 'scenes__choices')

class StoryCreateView(CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'story_templates/story_form.html'

class StoryUpdateView(UpdateView):
    model = Story
    form_class = StoryEditForm
    template_name = 'story_templates/story_form.html'
    context_object_name = 'story'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('scenes', 'scenes__choices')

class StoryDeleteView(DeleteView):
    model = Story
    template_name = 'story_templates/story_confirm_delete.html'
    success_url = reverse_lazy('stories:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['story'] = self.object
        context['cascade_warning'] = "Deleting this story will also delete all associated scenes and choices."
        return context

    def form_valid(self, form):
        story_title = self.object.story_title

        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this story because it has associated scenes or choices.")
            return redirect('stories:detail', pk=self.object.pk)

        messages.success(self.request, f'Story "{story_title}" has been deleted successfully.')
        return response

# Scene Views
class SceneCreateView(CreateView):
    model = Scene
    form_class = SceneForm
    template_name = 'story_templates/scene_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.story = get_object_or_404(Story, pk=kwargs['story_pk'])
        if not self.story.is_open:
            messages.warning(request, "Scenes can only be added to open stories.")
            return redirect('stories:detail', pk=self.story.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['story'] = self.story
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['story'] = self.story
        return context

    def form_valid(self, form):
        form.instance.story = self.story
        response = super().form_valid(form)
        messages.success(self.request, f'Scene "{form.instance.scene_title}" has been created successfully.')
        return response

class SceneDetailView(DetailView):
    model = Scene
    template_name = 'story_templates/scene_detail.html'
    context_object_name = 'scene'

    def get_queryset(self):
        return (Scene.objects.select_related('story').prefetch_related('lore_entries', 'choices'))

class SceneUpdateView(UpdateView):
    model = Scene
    form_class = SceneForm
    template_name = 'story_templates/scene_form.html'
    context_object_name = 'scene'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['story'] = self.object.story
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Scene "{form.instance.scene_title}" has been updated successfully.')
        return response

class SceneDeleteView(DeleteView):
    model = Scene
    template_name = 'story_templates/scene_confirm_delete.html'
    context_object_name = 'scene'

    def form_valid(self, form):
        self.story_pk = self.object.story_id
        scene_title = self.object.scene_title
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this scene because another object still references it.")
            return redirect('scenes:detail', pk=self.object.pk)

        messages.success(self.request, f'Scene "{scene_title}" has been deleted successfully.')
        return response

    def get_success_url(self):
        return reverse('stories:detail', kwargs={'pk': self.story_pk})

# Choice Views
def create_choice(request, scene_pk):
    scene = get_object_or_404(Scene, pk=scene_pk)

    if scene.scene_end:
        messages.warning(request, "Ending scenes can't have outgoing choices.")
        return redirect('scenes:detail', pk=scene.pk)

    if request.method == 'POST':
        form = ChoiceForm(request.POST, scene=scene)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.current_scene = scene
            choice.save()
            messages.success(request, f'Choice "{choice.text}" has been created successfully.')
            return redirect('scenes:detail', pk=scene.pk)
    else:
        form = ChoiceForm(initial={"current_scene": scene}, scene=scene)

    return render(request, 'story_templates/choice_form.html', {'form': form, 'scene': scene})

def delete_choice(request, choice_pk):
    choice = get_object_or_404(Choice, pk=choice_pk)
    scene = choice.current_scene

    if request.method == 'POST':
        choice.delete()
        messages.success(request, f'Choice "{choice.text}" has been deleted successfully.')
        return redirect('scenes:detail', pk=scene.pk)

    return render(request, 'story_templates/choice_confirm_delete.html', {'choice': choice, 'scene': scene})