from datetime import timedelta

from django.shortcuts import render, redirect
from django.http import Http404
from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.db.utils import OperationalError
from django.core.management import call_command
from todo.models import Task
import logging

logger = logging.getLogger(__name__)


# Create your views here.


def parse_due_at(due_at):
    if not due_at:
        return None
    parsed = parse_datetime(due_at)
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        return make_aware(parsed)
    return parsed


def index(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        title = request.POST.get('title', '').strip()
        if action == 'create' and title:
            due_at = request.POST.get('due_at')
            category = request.POST.get('category', '課題')
            task = Task(
                title=title,
                due_at=parse_due_at(due_at),
                category=category,
            )
            task.save()
        elif action in {'complete', 'delete'}:
            selected_ids = request.POST.getlist('task_ids')
            if selected_ids:
                if action == 'complete':
                    Task.objects.filter(pk__in=selected_ids).update(completed=True)
                elif action == 'delete':
                    Task.objects.filter(pk__in=selected_ids).delete()

    query = request.POST.get('q', request.GET.get('q', '')).strip()
    order = request.POST.get('order', request.GET.get('order'))

    try:
        if query:
            tasks = Task.objects.filter(title__icontains=query)
        else:
            tasks = Task.objects.all()
    except OperationalError as e:
        # If the DB schema is missing (e.g. new checkout without migrate),
        # try to apply migrations for development convenience and retry.
        logger.warning("OperationalError when querying tasks: %s", e)
        try:
            call_command('migrate', 'todo', '--noinput')
            # retry query after applying migrations
            if query:
                tasks = Task.objects.filter(title__icontains=query)
            else:
                tasks = Task.objects.all()
        except Exception as me:
            logger.exception("Failed to run migrations automatically: %s", me)
            # render a friendly error page with next steps
            return render(request, 'todo/error_migration.html', {'error': str(me)})

    if order == 'due':
        tasks = tasks.order_by('due_at')
    else:
        tasks = tasks.order_by('-posted_at')

    context = {
        'tasks': tasks,
        'query': query,
        'current_order': order or 'post',
        'category_choices': Task.CATEGORY_CHOICES,
    }
    return render(request, 'todo/index.html', context)

def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    context = {
        'task': task,
    }
    return render(request, 'todo/detail.html', context)


def dashboard(request):
    now = timezone.now()
    tasks = Task.objects.all()
    total_count = tasks.count()
    completed_count = tasks.filter(completed=True).count()
    overdue_count = tasks.filter(completed=False, due_at__lt=now).count()
    due_soon_count = tasks.filter(completed=False, due_at__gte=now, due_at__lte=now + timedelta(days=1)).count()
    no_deadline_count = tasks.filter(due_at__isnull=True).count()
    latest_tasks = tasks.order_by('-posted_at')[:5]

    context = {
        'total_count': total_count,
        'completed_count': completed_count,
        'overdue_count': overdue_count,
        'due_soon_count': due_soon_count,
        'no_deadline_count': no_deadline_count,
        'latest_tasks': latest_tasks,
    }
    return render(request, 'todo/dashboard.html', context)


def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.delete()
    return redirect(index)

def complete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.completed = not task.completed
    task.save()
    return redirect(detail, task_id)

def set_deadline(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == 'POST':
        due_at = request.POST.get('due_at')
        task.due_at = parse_due_at(due_at)
        task.save()
    return redirect(index)

def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == 'POST':
        task.title = request.POST['title']
        due_at = request.POST.get('due_at')
        category = request.POST.get('category', '課題')
        task.due_at = parse_due_at(due_at)
        task.category = category
        task.save()
        return redirect(detail, task_id)

    context = {
        'task': task,
        'category_choices': Task.CATEGORY_CHOICES,
    }
    return render(request, 'todo/edit.html', context)
