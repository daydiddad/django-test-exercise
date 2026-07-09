from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task


# Create your views here.


def index(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'create':
            due_at = request.POST.get('due_at')
            task = Task(
                title=request.POST['title'],
                due_at=make_aware(parse_datetime(due_at)) if due_at else None
            )
            task.save()
        else:
            selected_ids = request.POST.getlist('task_ids')
            if selected_ids:
                if action == 'complete':
                    Task.objects.filter(pk__in=selected_ids).update(completed=True)
                elif action == 'delete':
                    Task.objects.filter(pk__in=selected_ids).delete()

    query = request.GET.get('q', '').strip()
    order = request.GET.get('order')

    if query:
        tasks = Task.objects.filter(title__icontains=query)
    else:
        tasks = Task.objects.all()

    if order == 'due':
        tasks = tasks.order_by('due_at')
    else:
        tasks = tasks.order_by('-posted_at')

    context = {
        'tasks': tasks,
        'query': query,
        'current_order': order or 'post',
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

def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == 'POST':
        task.title = request.POST['title']
        task.due_at = make_aware(parse_datetime(request.POST['due_at']))
        task.save()
        return redirect(detail, task_id)

    context = {
        'task': task,
    }
    return render(request, 'todo/edit.html', context)
