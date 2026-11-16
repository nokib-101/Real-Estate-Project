from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AccountTests(TestCase):
    def register(self, password='Str0ng-Passw0rd!', **overrides):
        data = {'first_name': 'Bob', 'last_name': 'Buyer', 'username': 'bob',
                'email': 'bob@buyer.test', 'password': password, 'password2': password}
        data.update(overrides)
        return self.client.post(reverse('register'), data)

    def test_weak_password_is_rejected(self):
        self.register(password='123')
        self.assertFalse(User.objects.filter(username='bob').exists())

    def test_strong_password_registers(self):
        self.register()
        self.assertTrue(User.objects.filter(username='bob').exists())

    def test_missing_fields_do_not_crash(self):
        response = self.client.post(reverse('register'), {'username': 'bob'})
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('dashboard'), fetch_redirect_response=False)

    def test_logout_get_does_not_crash(self):
        self.assertEqual(self.client.get(reverse('logout')).status_code, 302)
