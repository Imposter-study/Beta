# Python Library
from uuid import UUID

# Third-Party Package
from django.test import TestCase

# Local Apps
from accounts.models import User
from characters.models import Character
from ..models import Room, Chat


class RoomModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="1234")
        self.character = Character.objects.create(name="Test_Char")

    def test_room_creation(self):
        room = Room.objects.create(user=self.user, character=self.character)
        self.assertIsInstance(room.uuid, UUID)
        self.assertFalse(room.fixation)
        self.assertEqual(str(room), f"{room.uuid} ({room.character})")


class ChatModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="1234")
        self.character = Character.objects.create(name="Test_Char")
        self.room = Room.objects.create(user=self.user, character=self.character)

    def test_chat_creation(self):
        chat = Chat.objects.create(room=self.room, content="Hello", role="user")
        self.assertEqual(chat.role, "user")
        self.assertTrue(chat.is_main)
        self.assertIsNone(chat.regeneration_group)
        self.assertEqual(
            str(chat), f"[{self.room.uuid}] {chat.role}: {chat.content[:30]}..."
        )

    def test_chat_ordering(self):
        Chat.objects.create(room=self.room, content="1", role="user")
        Chat.objects.create(room=self.room, content="2", role="ai")
        chats = list(self.room.chats.all())
        self.assertLessEqual(chats[0].created_at, chats[1].created_at)
