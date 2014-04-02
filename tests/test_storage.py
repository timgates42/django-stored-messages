# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import BaseTest

from django.contrib.messages.storage import default_storage
from django.test.utils import override_settings

from stored_messages import add_message, get_messages, STORED_ERROR, DEBUG, ERROR
from stored_messages.settings import stored_messages_settings

BackendClass = stored_messages_settings.STORAGE_BACKEND

import mock


class TestStorage(BaseTest):
    def test_store(self):
        self.request._messages = default_storage(self.request)
        self.request._messages.level = DEBUG
        add_message(self.request, STORED_ERROR, "an SOS to the world ☢")
        add_message(self.request, DEBUG, "this won't be persisted ☢")
        storage = get_messages(self.request)
        backend = BackendClass()
        self.assertEqual(len(storage), 2)
        self.assertEqual(len(backend.archive_list(self.user)), 1)

    def test_store_with_middleware(self):
        self.client.login(username='test_user', password='123456')
        self.client.get('/create')
        backend = BackendClass()
        inbox_msg = len(backend.inbox_list(self.user))
        self.assertEqual(inbox_msg, 1)
        self.client.get('/consume')
        self.assertEqual(len(backend.inbox_list(self.user)), 0)
        self.assertEqual(len(backend.archive_list(self.user)), 1)

    def test_store_keep_unread(self):
        self.client.login(username='test_user', password='123456')
        self.client.get('/create')
        self.client.get('/consume', data={'keep_storage': True})
        backend = BackendClass()
        self.assertEqual(len(backend.inbox_list(self.user)), 1)
        self.assertEqual(len(backend.archive_list(self.user)), 1)

    def test_store_anonymous(self):
        self.request.user = mock.MagicMock(wraps=self.user)
        self.request.user.is_anonymous.return_value = True
        self.request.user.is_authenticated.return_value = False
        self.request._messages = default_storage(self.request)
        add_message(self.request, STORED_ERROR, "an SOS to the world ☢")
        add_message(self.request, ERROR, "this error won't be persisted ☢")
        storage = get_messages(self.request)
        self.assertEqual(len(storage), 2)

    def test_add_empty(self):
        self.request._messages = default_storage(self.request)
        add_message(self.request, DEBUG, '')
        self.assertEqual(len(get_messages(self.request)), 0)

    def test_add_mixed(self):
        self.client.login(username='test_user', password='123456')
        self.client.get('/create_mixed')
        self.client.get('/consume')
        backend = BackendClass()
        self.assertEqual(len(backend.inbox_list(self.user)), 0)


@override_settings(STORED_MESSAGES={'STORAGE_BACKEND': 'stored_messages.backends.RedisBackend'})
class TestStorageWithRedis(TestStorage):
    pass
