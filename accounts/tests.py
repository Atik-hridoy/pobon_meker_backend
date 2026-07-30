from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.valid_payload = {
            "email": "testsecure@example.com",
            "password": "strongpassword123",
            "re_type_password": "strongpassword123"
        }

    def test_registration_success_format(self):
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIsNotNone(response.data['data'])
        self.assertIsNone(response.data['errors'])

    def test_registration_failure_format(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload['password'] = 'short'
        response = self.client.post(self.register_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIsNone(response.data['data'])
        self.assertIsNotNone(response.data['errors'])

    def test_login_format(self):
        # Register first
        self.client.post(self.register_url, self.valid_payload, format='json')
        
        # Then login
        login_payload = {
            "username": "testsecure@example.com",
            "password": "strongpassword123"
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertIsNone(response.data['errors'])
