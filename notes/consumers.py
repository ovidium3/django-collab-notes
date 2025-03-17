import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Note, Highlight, Comment

import logging
logger = logging.getLogger(__name__)

class NoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"connected to websocket")  # Debugging
        
        self.note_id = self.scope['url_route']['kwargs']['note_id']
        if not self.note_id:
            logger.error("No note_id found in scope")

        self.room_group_name = f'note_{self.note_id}'
        
        # join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket connected for note {self.note_id}")
        
        await self.accept()
    
    async def disconnect(self, close_code):
        print(f"disconnected from websocket")  # Debugging
        # leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # receive message from WebSocket
    async def receive(self, text_data):
        print(f"Received WebSocket message: {text_data}")  # Debugging
        
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'add_highlight':
            # save highlight to database
            highlight_id = await self.create_highlight(
                note_id=self.note_id,
                start_offset=data['start_offset'],
                end_offset=data['end_offset']
            )
            
            # send highlight to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'highlight_added',
                    'highlight_id': highlight_id,
                    'start_offset': data['start_offset'],
                    'end_offset': data['end_offset']
                }
            )
        
        elif action == 'add_comment':
            # save comment to database
            comment_id = await self.create_comment(
                highlight_id=data['highlight_id'],
                text=data['text']
            )
            
            # send comment to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'comment_added',
                    'comment_id': comment_id,
                    'highlight_id': data['highlight_id'],
                    'text': data['text']
                }
            )
        
        elif action == 'comment_updated':
            # update comment in database
            success = await self.update_comment(
                comment_id=data['comment_id'],
                text=data['text']
            )
            
            if success:
                # send updated comment to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'comment_updated',
                        'comment_id': data['comment_id'],
                        'highlight_id': data['highlight_id'],
                        'text': data['text']
                    }
                )
        
        elif action == 'delete_comment':
            # delete comment from database
            success, highlight_id = await self.delete_comment(
                comment_id=data['comment_id']
            )
            
            if success:
                # send delete notification to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'comment_deleted',
                        'comment_id': data['comment_id'],
                        'highlight_id': highlight_id
                    }
                )
        
        elif action == 'delete_highlight':
            # delete highlight and all associated comments
            success = await self.delete_highlight(
                highlight_id=data['highlight_id']
            )
            
            if success:
                # send delete notification to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'highlight_deleted',
                        'highlight_id': data['highlight_id']
                    }
                )
    
    # handler functions for different message types
    async def highlight_added(self, event):
        await self.send(text_data=json.dumps({
            'action': 'highlight_added',
            'highlight_id': event['highlight_id'],
            'start_offset': event['start_offset'],
            'end_offset': event['end_offset']
        }))
    
    async def comment_added(self, event):
        await self.send(text_data=json.dumps({
            'action': 'comment_added',
            'comment_id': event['comment_id'],
            'highlight_id': event['highlight_id'],
            'text': event['text']
        }))
    
    async def comment_updated(self, event):
        await self.send(text_data=json.dumps({
            'action': 'comment_updated',
            'comment_id': event['comment_id'],
            'highlight_id': event['highlight_id'],
            'text': event['text']
        }))
    
    async def comment_deleted(self, event):
        await self.send(text_data=json.dumps({
            'action': 'comment_deleted',
            'comment_id': event['comment_id'],
            'highlight_id': event['highlight_id']
        }))
    
    async def highlight_deleted(self, event):
        await self.send(text_data=json.dumps({
            'action': 'highlight_deleted',
            'highlight_id': event['highlight_id']
        }))
    
    # database operations
    @database_sync_to_async
    def create_highlight(self, note_id, start_offset, end_offset):
        note = Note.objects.get(id=note_id)
        highlight = Highlight.objects.create(
            note=note,
            start_offset=start_offset,
            end_offset=end_offset
        )
        return highlight.id
    
    @database_sync_to_async
    def create_comment(self, highlight_id, text):
        highlight = Highlight.objects.get(id=highlight_id)
        comment = Comment.objects.create(
            highlight=highlight,
            text=text
        )
        return comment.id
    
    @database_sync_to_async
    def update_comment(self, comment_id, text):
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.text = text
            comment.updated_at = timezone.now()
            comment.save()
            return True
        except Comment.DoesNotExist:
            return False
    
    @database_sync_to_async
    def delete_comment(self, comment_id):
        try:
            comment = Comment.objects.get(id=comment_id)
            highlight_id = comment.highlight_id
            comment.delete()
            return True, highlight_id
        except Comment.DoesNotExist:
            return False, None
    
    @database_sync_to_async
    def delete_highlight(self, highlight_id):
        try:
            highlight = Highlight.objects.get(id=highlight_id)
            highlight.delete()  # will also delete associated comments due to CASCADE
            return True
        except Highlight.DoesNotExist:
            return False
