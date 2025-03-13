from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Note, Highlight, Comment
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

def note_list(request):
    notes = Note.objects.all().order_by('-updated_at')
    return render(request, 'notes/note_list.html', {'notes': notes})

@csrf_exempt
def create_note(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        note = Note.objects.create(
            title=data.get('title', 'Untitled Note'),
            content=data.get('content', 'This is a collaborative note. Start editing!')
        )
        return JsonResponse({'success': True, 'note_id': note.id})
    return render(request, 'notes/create_note.html')

def editor(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    highlights = note.highlights.all()
    
    # Gather comments for each highlight
    highlight_comments = {}
    for highlight in highlights:
        highlight_comments[highlight.id] = list(highlight.comments.values('id', 'text'))
    
    context = {
        'note': note,
        'highlights': list(highlights.values('id', 'start_offset', 'end_offset')),
        'highlight_comments': highlight_comments
    }
    
    return render(request, 'notes/editor.html', context)
