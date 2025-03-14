from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # field for tracking if content is from an uploaded file
    is_uploaded = models.BooleanField(default=False)
    original_filename = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

class Highlight(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='highlights')
    start_offset = models.IntegerField()
    end_offset = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Highlight in {self.note.title} ({self.start_offset}-{self.end_offset})"

class Comment(models.Model):
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment on {self.highlight}"
