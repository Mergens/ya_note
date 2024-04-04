from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()
NOTE_TITLE = 'Заголовок для проверки'
NOTE_2_TITLE = 'Другой заголовок'
NOTE_TEXT = 'Текст для проверки'
NOTE_2_TEXT = 'Другой текст'

NOTE_SLUG = 'slug_for_test'


class TestNotecreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': NOTE_TITLE,
            'text': NOTE_TEXT,
            'slug': NOTE_SLUG
        }
        cls.form_new_data = {
            'title': NOTE_2_TITLE,
            'text': NOTE_2_TEXT,
            'slug': NOTE_SLUG,
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0)

    def test_user_can_create_note(self):
        self.auth_client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, NOTE_TEXT)
        self.assertEqual(note.title, NOTE_TITLE)
        self.assertEqual(note.slug, NOTE_SLUG)
        self.assertEqual(note.author, self.user)

    def test_not_possible_to_create_same_slug(self):
        self.auth_client.post(self.url, data=self.form_data)
        note = Note.objects.get()
        response = self.auth_client.post(self.url, data=self.form_new_data)
        self.assertFormError(
            response, 'form', 'slug',
            errors=(note.slug + WARNING)
        )

    def test_slugify(self):
        self.form_data.pop('slug')
        self.auth_client.post(self.url, data=self.form_data)
        note = Note.objects.get()
        self.assertEqual(note.slug, slugify(note.title))


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Заметка'
    NEW_NOTE_TEXT = 'Другая заметка'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug=NOTE_SLUG)
        cls.success_url = reverse('notes:success')
        cls.note_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'title': NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': NOTE_SLUG
        }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
