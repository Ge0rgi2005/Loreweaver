from django.contrib import messages
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from .forms import StoryEditForm, StoryForm, SceneForm, ChoiceForm, StoryFilterForm
from .models import Story, Scene, Choice
from .services import check_story_health

MAX_PLAY_PATH_LENGTH = 200


def story_health(request, pk):
    story = get_object_or_404(Story, pk=pk)
    report = check_story_health(story)
    return render(
        request,
        "story_templates/story_health.html",
        {"story": story, "report": report},
    )


def _play_path(request, story, start_scene):
    session_key = f"play_{story.pk}"
    stored_path = request.session.get(session_key)
    if stored_path is None:
        path = [start_scene.pk]
        request.session[session_key] = path
        return path

    invalid_path = (
        not isinstance(stored_path, list)
        or not stored_path
        or any(type(scene_id) is not int for scene_id in stored_path)
        or len(stored_path) > MAX_PLAY_PATH_LENGTH
    )
    if invalid_path:
        valid_scene_ids = set()
    else:
        valid_scene_ids = set(
            Scene.objects.filter(
                story=story, pk__in=stored_path
            ).values_list("pk", flat=True)
        )

    if invalid_path or valid_scene_ids != set(stored_path):
        path = [start_scene.pk]
        request.session[session_key] = path
        return path
    return stored_path


def play_story(request, pk):
    story = get_object_or_404(Story, pk=pk)
    start_scene = story.scenes.filter(scene_start=True).first()
    if start_scene is None:
        request.session.pop(f"play_{story.pk}", None)
        messages.warning(request, "This story has no starting scene yet.")
        return redirect("stories:detail", pk=story.pk)

    path = _play_path(request, story, start_scene)
    scenes_by_id = {
        scene.pk: scene
        for scene in Scene.objects.filter(story=story, pk__in=path)
    }
    visited_scenes = [scenes_by_id[scene_id] for scene_id in path]
    scene = visited_scenes[-1]
    choices = scene.choices.select_related("next_scene").all()
    finished = scene.scene_end

    return render(
        request,
        "story_templates/story_play.html",
        {
            "story": story,
            "scene": scene,
            "choices": choices,
            "path": visited_scenes,
            "steps": len(path) - 1,
            "finished": finished,
            "path_limit_reached": len(path) >= MAX_PLAY_PATH_LENGTH,
        },
    )


def choose_story_choice(request, pk, choice_pk):
    story = get_object_or_404(Story, pk=pk)
    if request.method != "POST":
        return redirect("stories:play", pk=story.pk)

    start_scene = story.scenes.filter(scene_start=True).first()
    if start_scene is None:
        request.session.pop(f"play_{story.pk}", None)
        messages.warning(request, "This story has no starting scene yet.")
        return redirect("stories:detail", pk=story.pk)

    path = _play_path(request, story, start_scene)
    current_scene_id = path[-1]
    choice = get_object_or_404(Choice, pk=choice_pk)
    if (
        choice.current_scene_id != current_scene_id
        or choice.next_scene_id is None
        or choice.next_scene.story_id != story.pk
    ):
        messages.warning(request, "That choice isn't available from the current scene.")
        return redirect("stories:play", pk=story.pk)
    if len(path) >= MAX_PLAY_PATH_LENGTH:
        messages.warning(request, "The play path has reached its maximum length.")
        return redirect("stories:play", pk=story.pk)

    request.session[f"play_{story.pk}"] = [*path, choice.next_scene_id]
    return redirect("stories:play", pk=story.pk)


def restart_story(request, pk):
    story = get_object_or_404(Story, pk=pk)
    if request.method != "POST":
        return redirect("stories:play", pk=story.pk)

    session_key = f"play_{story.pk}"
    request.session.pop(session_key, None)
    start_scene = story.scenes.filter(scene_start=True).first()
    if start_scene is None:
        messages.warning(request, "This story has no starting scene yet.")
        return redirect("stories:detail", pk=story.pk)

    request.session[session_key] = [start_scene.pk]
    return redirect("stories:play", pk=story.pk)

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