import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Note, Highlight, Comment

class NoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.note_id = self.scope['url_route']['kwargs']['note_id']
        self.room_group_name = f'note_{self.note_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'add_highlight':
            # Save highlight to database
            highlight_id = await self.create_highlight(
                note_id=self.note_id,
                start_offset=data['start_offset'],
                end_offset=data['end_offset']
            )
            
            # Send highlight to room group
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
            # Save comment to database
            comment_id = await self.create_comment(
                highlight_id=data['highlight_id'],
                text=data['text']
            )
            
            # Send comment to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'comment_added',
                    'comment_id': comment_id,
                    'highlight_id': data['highlight_id'],
                    'text': data['text']
                }
            )
    
    # Handler for highlight_added messages
    async def highlight_added(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'action': 'highlight_added',
            'highlight_id': event['highlight_id'],
            'start_offset': event['start_offset'],
            'end_offset': event['end_offset']
        }))
    
    # Handler for comment_added messages
    async def comment_added(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'action': 'comment_added',
            'comment_id': event['comment_id'],
            'highlight_id': event['highlight_id'],
            'text': event['text']
        }))
    
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
