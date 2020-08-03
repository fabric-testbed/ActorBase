#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Komal Thareja (kthare10@renci.org)
from __future__ import annotations
from typing import TYPE_CHECKING

from fabric.actor.core.manage.authority_management_object import AuthorityManagementObject
from fabric.actor.core.apis.i_mgmt_authority import IMgmtAuthority
from fabric.actor.core.manage.local.local_server_actor import LocalServerActor

if TYPE_CHECKING:
    from fabric.actor.core.manage.management_object import ManagementObject
    from fabric.actor.security.auth_token import AuthToken
    from fabric.actor.core.util.id import ID
    from fabric.actor.core.manage.messages.unit_mng import UnitMng
    from fabric.actor.core.apis.i_mgmt_actor import IMgmtActor


class LocalAuthority(LocalServerActor, IMgmtAuthority):
    def __init__(self, manager: ManagementObject = None, auth: AuthToken = None):
        super().__init__(manager, auth)

        if not isinstance(manager, AuthorityManagementObject):
            raise Exception("Invalid manager object. Required: {}".format(type(AuthorityManagementObject)))

    def get_authority_reservations(self) -> list:
        self.clear_last()
        try:
            result = self.manager.get_authority_reservations(self.auth)
            self.last_status = result.status
            if result.status.get_code() == 0:
                return result.result
        except Exception as e:
            self.last_exception = e

        return None

    def get_reservation_units(self, rid: ID) -> list:
        self.clear_last()
        try:
            result = self.manager.get_reservation_units(self.auth, rid)
            self.last_status = result.status
            if result.status.get_code() == 0:
                return result.result
        except Exception as e:
            self.last_exception = e

        return None

    def get_reservation_unit(self, uid: ID) -> UnitMng:
        self.clear_last()
        try:
            result = self.manager.get_reservation_unit(self.auth, uid)
            self.last_status = result.status
            if result.get_status().get_code() == 0:
                return self.get_first(result.result)
        except Exception as e:
            self.last_exception = e

        return None

    def clone(self) -> IMgmtActor:
        return LocalAuthority(self.manager, self.auth)