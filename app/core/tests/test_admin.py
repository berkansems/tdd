"""
test for django admin modifications.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model


class AdminSiteTests(TestCase):

    def setUp(self):
        '''
        this will run before every test
        to test the admin site.
        :return:
        '''
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin_user@example.com',
            password='PASSWORD'
        )
        # force authentication to the user
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='PASSWORD2',
        )

    def test_users_listed(self):
        # reverse by django default url which is like {{ app_label }}_{{ model_name }}_changelist
        # https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#reversing-admin-urls
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)
        self.assertContains(res, self.user.email)
        self.assertContains(res, self.user.is_active)
        self.assertNotContains(res, self.user.is_staff)
        self.assertContains(res, self.admin_user.email)

    def test_user_change_page(self):
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.user.email)

    def test_create_user_page(self):
        url = reverse('admin:core_user_add')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
