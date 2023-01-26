from django import test
from django.test import Client
from django.urls import reverse
from unittest import TestCase


class UrlsTest(TestCase):

    c = Client()

    def setUp(self):
        self.c.login(username='Jarno', password='Password')

    def test_home(self):
        response = self.c.get(reverse('index'))
        self.assertEquals(response.status_code, 200)

    def test_details(self):
        response = self.c.get(reverse('details', args=[1000]))
        self.assertEquals(response.status_code, 200)

    def test_stats(self):
        response = self.c.get(reverse('stats'))
        self.assertEquals(response.status_code, 200)

    def test_tools(self):
        response = self.c.get(reverse('tools'))
        self.assertEquals(response.status_code, 200)

    def test_nuaanwezig(self):
        response = self.c.get(reverse('nu_aanwezig'))
        self.assertEquals(response.status_code, 200)

    def test_overuren(self):
        response = self.c.get(reverse('overuren'))
        self.assertEquals(response.status_code, 200)
