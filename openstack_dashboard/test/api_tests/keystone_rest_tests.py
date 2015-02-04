# Copyright 2014, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mock
import testtools

from django.conf import settings

from openstack_dashboard.api.rest import keystone

from rest_test_utils import construct_request   # noqa


class KeystoneRestTestCase(testtools.TestCase):
    def assertStatusCode(self, response, expected_code):
        if response.status_code == expected_code:
            return
        self.fail('status code %r != %r: %s' % (response.status_code,
                                                expected_code,
                                                response.content))

    #
    # Users
    #
    @mock.patch.object(keystone.api, 'keystone')
    def test_user_get(self, kc):
        request = construct_request()
        kc.user_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.User().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"name": "Ni!"}')
        kc.user_get.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_get_current(self, kc):
        request = construct_request(**{'user.id': 'current_id'})
        kc.user_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.User().get(request, 'current')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"name": "Ni!"}')
        kc.user_get.assert_called_once_with(request, 'current_id')
        kc.user_get.assert_not_called()

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_get_list(self, kc):
        request = construct_request(**{
            'session.get': mock.Mock(return_value='the_domain'),
            'GET': {},
        })
        kc.user_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Users().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"name": "Ni!"}, {"name": "Ptang!"}]}')
        kc.user_list.assert_called_once_with(request, project=None,
                                             domain='the_domain', group=None)

    def test_user_create_full(self):
        self._test_user_create(
            '{"name": "bob", '
            '"password": "sekrit", "project_id": "project123", '
            '"email": "spam@company.example"}',
            {
                'name': 'bob',
                'password': 'sekrit',
                'email': 'spam@company.example',
                'project': 'project123',
                'domain': 'the_domain',
                'enabled': True
            }
        )

    def test_user_create_existing_role(self):
        self._test_user_create(
            '{"name": "bob", '
            '"password": "sekrit", "project_id": "project123", '
            '"email": "spam@company.example"}',
            {
                'name': 'bob',
                'password': 'sekrit',
                'email': 'spam@company.example',
                'project': 'project123',
                'domain': 'the_domain',
                'enabled': True
            }
        )

    def test_user_create_partial(self):
        self._test_user_create(
            '{"name": "bob"}',
            {
                'name': 'bob',
                'password': None,
                'email': None,
                'project': None,
                'domain': 'the_domain',
                'enabled': True
            }
        )

    @mock.patch.object(keystone.api, 'keystone')
    def _test_user_create(self, supplied_body, expected_call, kc):
        request = construct_request(body=supplied_body)
        kc.get_default_domain.return_value = mock.Mock(**{'id': 'the_domain'})
        kc.user_create.return_value.id = 'user123'
        kc.user_create.return_value = mock.Mock(**{
            'id': 'user123',
            'to_dict.return_value': {'id': 'user123', 'name': 'bob'}
        })

        response = keystone.Users().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/users/user123')
        self.assertEqual(response.content, '{"id": "user123", '
                         '"name": "bob"}')
        kc.user_create.assert_called_once_with(request, **expected_call)

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_delete_many(self, kc):
        request = construct_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Users().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.user_delete.assert_has_mock.calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_delete(self, kc):
        request = construct_request()
        response = keystone.User().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.user_delete.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_patch_password(self, kc):
        request = construct_request(body='''
            {"password": "sekrit"}
        ''')
        response = keystone.User().patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.user_update_password.assert_called_once_with(request,
                                                        'user123',
                                                        password='sekrit')

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_patch_enabled(self, kc):
        request = construct_request(body='''
            {"enabled": false}
        ''')
        response = keystone.User().patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.user_update_enabled.assert_called_once_with(request,
                                                       'user123',
                                                       enabled=False)

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_patch_project(self, kc):
        request = construct_request(body='''
            {"project_id": "other123"}
        ''')
        response = keystone.User().patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.user_update_tenant.assert_called_once_with(request,
                                                      'user123',
                                                      project='other123')

    @mock.patch.object(keystone.api, 'keystone')
    def test_user_patch_multiple(self, kc):
        request = construct_request(body='''
            {"project_id": "other123", "enabled": false}
        ''')
        response = keystone.User().patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.user_update.assert_called_once_with(request,
                                               'user123',
                                               enabled=False,
                                               password=None,
                                               project='other123')

    #
    # Roles
    #
    @mock.patch.object(keystone.api, 'keystone')
    def test_role_get(self, kc):
        request = construct_request()
        kc.role_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Role().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"name": "Ni!"}')
        kc.role_get.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_get_default(self, kc):
        request = construct_request()
        kc.get_default_role.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Role().get(request, 'default')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"name": "Ni!"}')
        kc.get_default_role.assert_called_once_with(request)
        kc.role_get.assert_not_called()

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_get_list(self, kc):
        request = construct_request(**{'GET': {}})
        kc.role_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Roles().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"name": "Ni!"}, {"name": "Ptang!"}]}')
        kc.role_list.assert_called_once_with(request)

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_get_for_user(self, kc):
        request = construct_request(**{'GET': {'user_id': 'user123',
                                    'project_id': 'project123'}})
        kc.roles_for_user.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Roles().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"name": "Ni!"}, {"name": "Ptang!"}]}')
        kc.roles_for_user.assert_called_once_with(request, 'user123',
                                                  'project123')

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_create(self, kc):
        request = construct_request(body='''
            {"name": "bob"}
        ''')
        kc.role_create.return_value.id = 'role123'
        kc.role_create.return_value.to_dict.return_value = {
            'id': 'role123', 'name': 'bob'
        }

        response = keystone.Roles().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/roles/role123')
        self.assertEqual(response.content, '{"id": "role123", "name": "bob"}')
        kc.role_create.assert_called_once_with(request, 'bob')

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_grant(self, kc):
        request = construct_request(body='''
            {"action": "grant", "data": {"user_id": "user123",
            "role_id": "role123", "project_id": "project123"}}
        ''')
        response = keystone.ProjectRole().put(request, "project1", "role2",
                                              "user3")
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.add_tenant_user_role.assert_called_once_with(request, 'project1',
                                                        'user3', 'role2')

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_delete_many(self, kc):
        request = construct_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Roles().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.role_delete.assert_has_mock.calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_delete(self, kc):
        request = construct_request()
        response = keystone.Role().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.role_delete.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_role_patch(self, kc):
        request = construct_request(body='{"name": "spam"}')
        response = keystone.Role().patch(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.role_update.assert_called_once_with(request,
                                               'the_id',
                                               'spam')

    #
    # Domains
    #
    @mock.patch.object(keystone.api, 'keystone')
    def test_domain_get(self, kc):
        request = construct_request()
        kc.domain_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Domain().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"name": "Ni!"}')
        kc.domain_get.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_domain_get_default(self, kc):
        request = construct_request()
        kc.get_default_domain.return_value.to_dict.return_value = {
            'name': 'Ni!'
        }
        response = keystone.Domain().get(request, 'default')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"name": "Ni!"}')
        kc.get_default_domain.assert_called_once_with(request)
        kc.domain_get.assert_not_called()

    @mock.patch.object(keystone.api, 'keystone')
    def test_domain_get_list(self, kc):
        request = construct_request()
        kc.domain_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Domains().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content,
                         '{"items": [{"name": "Ni!"}, {"name": "Ptang!"}]}')
        kc.domain_list.assert_called_once_with(request)

    def test_domain_create_full(self):
        self._test_domain_create(
            '{"name": "bob", '
            '"description": "sekrit", "enabled": false}',
            {
                'description': 'sekrit',
                'enabled': False
            }
        )

    def test_domain_create_partial(self):
        self._test_domain_create(
            '{"name": "bob"}',
            {
                'description': None,
                'enabled': True
            }
        )

    @mock.patch.object(keystone.api, 'keystone')
    def _test_domain_create(self, supplied_body, expected_call, kc):
        request = construct_request(body=supplied_body)
        kc.domain_create.return_value.id = 'domain123'
        kc.domain_create.return_value.to_dict.return_value = {
            'id': 'domain123', 'name': 'bob'
        }

        response = keystone.Domains().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/domains/domain123')
        self.assertEqual(response.content, '{"id": "domain123", '
                         '"name": "bob"}')
        kc.domain_create.assert_called_once_with(request, 'bob',
                                                 **expected_call)

    @mock.patch.object(keystone.api, 'keystone')
    def test_domain_delete_many(self, kc):
        request = construct_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Domains().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.domain_delete.assert_has_mock.calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @mock.patch.object(keystone.api, 'keystone')
    def test_domain_delete(self, kc):
        request = construct_request()
        response = keystone.Domain().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.domain_delete.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_domain_patch(self, kc):
        request = construct_request(body='{"name": "spam"}')
        response = keystone.Domain().patch(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.domain_update.assert_called_once_with(request,
                                                 'the_id',
                                                 name='spam',
                                                 description=None,
                                                 enabled=None)

    #
    # Projects
    #
    @mock.patch.object(keystone.api, 'keystone')
    def test_project_get(self, kc):
        request = construct_request()
        kc.tenant_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Project().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"name": "Ni!"}')
        kc.tenant_get.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_project_get_list(self, kc):
        request = construct_request(**{'GET': {}})
        kc.tenant_list.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ], False)
        with mock.patch.object(settings, 'DEBUG', True):
            response = keystone.Projects().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, '{"has_more": false, '
                         '"items": [{"name": "Ni!"}, {"name": "Ptang!"}]}')
        kc.tenant_list.assert_called_once_with(request, paginate=False,
                                               marker=None, domain=None,
                                               user=None, admin=True)

    def test_project_create_full(self):
        self._test_project_create(
            '{"name": "bob", '
            '"domain_id": "domain123", "description": "sekrit", '
            '"enabled": false}',
            {
                'description': 'sekrit',
                'domain': 'domain123',
                'enabled': False
            }
        )

    def test_project_create_partial(self):
        self._test_project_create(
            '{"name": "bob"}',
            {
                'description': None,
                'domain': None,
                'enabled': True
            }
        )

    @mock.patch.object(keystone.api, 'keystone')
    def _test_project_create(self, supplied_body, expected_call, kc):
        request = construct_request(body=supplied_body)
        kc.tenant_create.return_value.id = 'project123'
        kc.tenant_create.return_value.to_dict.return_value = {
            'id': 'project123', 'name': 'bob'
        }

        response = keystone.Projects().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/projects/project123')
        self.assertEqual(response.content, '{"id": "project123", '
                         '"name": "bob"}')
        kc.tenant_create.assert_called_once_with(request, 'bob',
                                                 **expected_call)

    @mock.patch.object(keystone.api, 'keystone')
    def test_project_delete_many(self, kc):
        request = construct_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Projects().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.tenant_delete.assert_has_mock.calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @mock.patch.object(keystone.api, 'keystone')
    def test_project_delete(self, kc):
        request = construct_request()
        response = keystone.Project().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.tenant_delete.assert_called_once_with(request, 'the_id')

    @mock.patch.object(keystone.api, 'keystone')
    def test_project_patch(self, kc):
        # nothing in the Horizon code documents what additional parameters are
        # allowed, so we'll just assume GIGO
        request = construct_request(body='''
            {"name": "spam", "domain_id": "domain123", "foo": "bar"}
        ''')
        response = keystone.Project().patch(request, 'spam123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, '')
        kc.tenant_update.assert_called_once_with(request,
                                                 'spam123',
                                                 name='spam', foo='bar',
                                                 description=None,
                                                 domain='domain123',
                                                 enabled=None)
