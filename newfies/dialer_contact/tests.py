#
# Newfies-Dialer License
# http://www.newfies-dialer.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.contrib.auth.models import User
from django.template import Template, Context, TemplateSyntaxError
from django.test import TestCase
from dialer_contact.models import Phonebook, Contact
from dialer_contact.forms import Contact_fileImport, \
                                 PhonebookForm, \
                                 ContactForm, \
                                 ContactSearchForm
from dialer_contact.views import phonebook_grid, phonebook_list, \
                         phonebook_add, phonebook_change, phonebook_del,\
                         contact_grid, contact_list, contact_add,\
                         contact_change, contact_del, contact_import
from dialer_contact.tasks import collect_subscriber_optimized, \
                                 import_phonebook
from common.utils import BaseAuthenticatedClient
from datetime import datetime



class DialerContactView(BaseAuthenticatedClient):
    """Test cases for Phonebook, Contact, Campaign, CampaignSubscriber
       Admin Interface.
    """

    def test_admin_phonebook_view_list(self):
        """Test Function to check admin phonebook list"""
        # the breakpoint will be here
        # import pdb
        # pdb.set_trace()

        response = self.client.get("/admin/dialer_contact/phonebook/")
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_phonebook_view_add(self):
        """Test Function to check admin phonebook add"""
        response = self.client.get("/admin/dialer_contact/phonebook/add/")
        self.assertEqual(response.status_code, 200)

    def test_admin_contact_view_list(self):
        """Test Function to check admin contact list"""
        response = self.client.get("/admin/dialer_contact/contact/")
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_contact_view_add(self):
        """Test Function to check admin contact add"""
        response = self.client.get("/admin/dialer_contact/contact/add/")
        self.assertEqual(response.status_code, 200)

    def test_admin_contact_view_import(self):
        """Test Function to check admin import contact"""
        response =\
            self.client.get('/admin/dialer_contact/contact/import_contact/')
        self.failUnlessEqual(response.status_code, 200)


class DialerContactCustomerView(BaseAuthenticatedClient):
    """Test cases for Phonebook, Contact, Campaign, CampaignSubscriber
       Customer Interface.
    """

    fixtures = ['auth_user.json', 'phonebook.json', 'contact.json']

    def test_phonebook_view_list(self):
        """Test Function to check phonebook list"""
        response = self.client.get('/phonebook/')
        self.assertEqual(response.context['module'], 'phonebook_list')
        self.assertTemplateUsed(response, 'frontend/phonebook/list.html')

        request = self.factory.get('/phonebook_grid/')
        request.user = self.user
        request.session = {}
        response = phonebook_list(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/phonebook/')
        request.user = self.user
        request.session = {}
        response = phonebook_list(request)
        self.assertEqual(response.status_code, 200)

    def test_phonebook_view_add(self):
        """Test Function to check add phonebook"""
        request = self.factory.post('/phonebook/add/', data={
            'name': 'My Phonebook',
            'description': 'phonebook',
            }, follow=True)
        request.user = self.user
        request.session = {}
        response = phonebook_add(request)
        self.assertEqual(response['Location'], '/phonebook/')
        self.assertEqual(response.status_code, 302)

        out = Template(
                '{% block content %}'
                    '{% if msg %}'
                        '{{ msg|safe }}'
                    '{% endif %}'
                '{% endblock %}'
            ).render(Context({
                'msg': request.session.get('msg'),
            }))
        self.assertEqual(out, '"My Phonebook" is added.')

        resp = self.client.post('/phonebook/add/',
            data={
                'name': '',
                'description': 'phonebook',
            })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['form']['name'].errors,
                         [u'This field is required.'])


    def test_phonebook_view_update(self):
        """Test Function to check update phonebook"""
        response = self.client.get('/phonebook/1/')
        self.assertEqual(response.context['action'], 'update')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/phonebook/change.html')

        request = self.factory.post('/phonebook/1/', data={
            'name': 'Default_Phonebook',
            }, follow=True)
        request.user = self.user
        request.session = {}
        response = phonebook_change(request, 1)
        self.assertEqual(response['Location'], '/phonebook/')
        self.assertEqual(response.status_code, 302)

        out = Template(
            '{% block content %}'
                '{% if msg %}'
                    '{{ msg|safe }}'
                '{% endif %}'
            '{% endblock %}'
        ).render(Context({
            'msg': request.session.get('msg'),
            }))
        self.assertEqual(out, '"Default_Phonebook" is updated.')

    def test_phonebook_view_delete(self):
        """Test Function to check delete phonebook"""
        request = self.factory.post('/phonebook/del/1/')
        request.user = self.user
        request.session = {}
        response = phonebook_del(request, 1)
        self.assertEqual(response['Location'], '/phonebook/')
        self.assertEqual(response.status_code, 302)

        out = Template(
                '{% block content %}'
                    '{% if msg %}'
                        '{{ msg|safe }}'
                    '{% endif %}'
                '{% endblock %}'
            ).render(Context({
                'msg': request.session.get('msg'),
            }))
        self.assertEqual(out, '"Default_Phonebook" is deleted.')

    def test_contact_view_list(self):
        """Test Function to check Contact list"""
        response = self.client.get('/contact/')
        self.assertEqual(response.context['module'], 'contact_list')
        self.assertTrue(response.context['form'], ContactSearchForm(self.user))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'frontend/contact/list.html')

        request = self.factory.get('/contact_grid/')
        request.user = self.user
        request.session = {}
        response = phonebook_list(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/contact/',
            data={'from_date': datetime.now(),
                  'to_date': datetime.now(),
                  'name': '123'})
        request.user = self.user
        request.session = {}
        response = contact_list(request)
        self.assertEqual(response.status_code, 200)

    def test_contact_view_add(self):
        """Test Function to check add Contact"""
        response = self.client.get('/contact/add/')
        self.assertEqual(response.context['action'], 'add')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/contact/add/',
            data={'phonebook_id': '1', 'contact': '1234',
                  'last_name': 'xyz', 'first_name': 'abc',
                  'status': '1'})
        self.assertEqual(response.context['action'], 'add')
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/contact/add/')
        request.user = self.user
        request.session = {}
        response = contact_add(request)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/contact/add/',
                                    data={'contact': '1234'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['phonebook'].errors,
                         [u'This field is required.'])

    def test_contact_view_update(self):
        """Test Function to check update Contact"""
        response = self.client.get('/contact/1/')
        self.assertTrue(response.context['form'], ContactForm(self.user))
        self.assertEqual(response.context['action'], 'update')
        self.assertTemplateUsed(response, 'frontend/contact/change.html')

        request = self.factory.get('/contact/1/')
        request.user = self.user
        request.session = {}
        response = contact_change(request, 1)
        self.assertEqual(response.status_code, 200)

    def test_contact_view_delete(self):
        """Test Function to check delete contact"""
        request = self.factory.get('/contact/del/1/')
        request.user = self.user
        request.session = {}
        response = contact_del(request, 1)
        self.assertEqual(response.status_code, 302)

    def test_contact_view_import(self):
        """Test Function to check import Contact"""
        response = self.client.get('/contact/import/')
        self.assertTrue(response.context['form'], Contact_fileImport(self.user))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,
                'frontend/contact/import_contact.html')

        response = self.client.post('/contact/import/',
            data={'phonebook_id': '1'})
        self.assertEqual(response.status_code, 200)

        request = self.factory.get('/contact/import/')
        request.user = self.user
        request.session = {}
        response = contact_import(request)
        self.assertEqual(response.status_code, 200)



class DialerContactCeleryTaskTestCase(TestCase):
    """Test cases for celery task"""

    fixtures = ['gateway.json', 'voiceapp.json', 'auth_user.json',
                'dialer_setting.json', 'contenttype.json',
                'phonebook.json', 'contact.json',
                'campaign.json', 'campaign_subscriber.json',
                'user_profile.json']

    def test_collect_subscriber_optimized(self):
        """Test that the ``collect_subscriber_optimized``
        task runs with no errors, and returns the correct result."""
        result = collect_subscriber_optimized.delay(1)
        self.assertEqual(result.successful(), True)

    def test_import_phonebook(self):
        """Test that the ``import_phonebook``
        task runs with no errors, and returns the correct result."""
        result = import_phonebook.delay(1, 1)
        self.assertEqual(result.successful(), True)


class DialerContactModel(TestCase):
    """Test Phonebook, Contact models"""

    fixtures = ['auth_user.json', 'phonebook.json', 'contact.json']

    def setUp(self):
        self.user = User.objects.get(username='admin')

        # Phonebook model
        self.phonebook = Phonebook(
            name='test_phonebook',
            user=self.user,
        )
        self.phonebook.save()

        # Contact model
        self.contact = Contact(
            phonebook=self.phonebook,
            contact=123456789,
        )
        self.contact.save()

    def test_phonebook_form(self):
        self.assertEqual(self.phonebook.name, 'test_phonebook')
        form = PhonebookForm({'name': 'sample_phonebook'})
        obj = form.save(commit=False)
        obj.user = self.user
        obj.save()

        form = PhonebookForm(instance=self.phonebook)
        self.assertTrue(isinstance(form.instance, Phonebook))

    def test_contact_form(self):
        self.assertEqual(self.contact.phonebook, self.phonebook)
        form = ContactForm(self.user)
        form.contact = '123456'
        obj = form.save(commit=False)
        obj.phonebook = self.phonebook
        obj.save()

        form = ContactForm(self.user, instance=self.contact)
        self.assertTrue(isinstance(form.instance, Contact))


    def teardown(self):
        self.phonebook.delete()
        self.contact.delete()
