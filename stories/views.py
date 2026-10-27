from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect, request
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from .forms import StoryForm, SceneForm, ChoiceForm, StoryFilterForm
from .models import Story, Scene, Choice

# Story Views
class StoryListView(ListView):
    model = Story
    template_name = 'stories/story_list.html'
    context_object_name = 'stories'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_form = StoryFilterForm(self.request.GET)
        if filter_form.is_valid():
            genre = filter_form.cleaned_data.get('story_genre')
            status = filter_form.cleaned_data.get('story_status')
            author = filter_form.cleaned_data.get('story_author')
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
        sort_by = self.request.GET.get('sort_by')
        if sort_by in sort_options:
            queryset = queryset.order_by(sort_options[sort_by])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = StoryFilterForm(self.request.GET)
        return context

class StoryCreateView(CreateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'

class StoryUpdateView(UpdateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'

    def get_queryset(self):
        return super().get_queryset().prefetch_related('scenes', 'scenes__choices')

class StoryUpdateView(UpdateView):
    model = Story
    form_class = StoryForm
    template_name = 'stories/story_form.html'
    context_object_name = 'story'

class StoryDeleteView(DeleteView):
    model = Story
    template_name = 'stories/story_confirm_delete.html'
    success_url = reverse_lazy('story_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['story'] = self.object
        context['cascade_warning'] = "Deleting this story will also delete all associated scenes and choices."
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        story_title = self.object.story_title

        try:
            response = super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this story because it has associated scenes or choices.")
            return redirect('stories:detail', pk=self.object.pk)

        messages.success(self.request, f'Story "{story_title}" has been deleted successfully.')
        return response

# Scene Views
class SceneCreateView(CreateView):
    model = Scene
    form_class = SceneForm
    template_name = 'stories/scene_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.story = get_object_or_404(Story, pk=kwargs['story_pk'])
        if str(self.story.story_status).lower() != 'open':
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
    template_name = 'stories/scene_detail.html'
    context_object_name = 'scene'

    def get_queryset(self):
        return (Scene.objects.select_related('story').prefetch_related('lore_entries', 'choices'))

class SceneUpdateView(UpdateView):
    model = Scene
    form_class = SceneForm
    template_name = 'stories/scene_form.html'
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
    template_name = 'stories/scene_confirm_delete.html'
    context_object_name = 'scene'

    def form_valid(self, form):
        self.story_pk = self.object.story_id
        scene_title = self.object.scene_title
        try:
            response = super().delete(self.request, *self.args, **self.kwargs)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this scene because another object still references it.")
            return redirect('stories:scene_detail', pk=self.object.pk)

        messages.success(self.request, f'Scene "{scene_title}" has been deleted successfully.')
        return response

    def get_success_url(self):
        return reverse('stories:detail', kwargs={'pk': self.story_pk})

# Choice Views
def create_choice(request, scene_pk):
    scene = get_object_or_404(Scene, pk=scene_pk)

    if scene.scene_end:
        messages.warning(request, "Ending scenes can't have outgoing choices.")
        return redirect('stories:scene_detail', pk=scene.pk)

    if request.method == 'POST':
        form = ChoiceForm(request.POST, scene=scene)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.current_scene = scene
            choice.save()
            messages.success(request, f'Choice "{choice.text}" has been created successfully.')
            return redirect('stories:scene_detail', pk=scene.pk)
    else:
        form = ChoiceForm(initial={"current_scene": scene})

    return render(request, 'stories/choice_form.html', {'form': form, 'scene': scene})

def delete_choice(request, choice_pk):
    choice = get_object_or_404(Choice, pk=choice_pk)
    scene = choice.current_scene

    if request.method == 'POST':
        choice.delete()
        messages.success(request, f'Choice "{choice.text}" has been deleted successfully.')
        return redirect('stories:scene_detail', pk=scene.pk)

    return render(request, 'stories/choice_confirm_delete.html', {'choice': choice})