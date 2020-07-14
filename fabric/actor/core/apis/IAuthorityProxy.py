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
if TYPE_CHECKING:
    from fabric.actor.core.apis.IControllerCallbackProxy import IControllerCallbackProxy
    from fabric.actor.core.apis.IControllerReservation import IControllerReservation
    from fabric.actor.core.apis.IRPCRequestState import IRPCRequestState
    from fabric.actor.security.AuthToken import AuthToken

from fabric.actor.core.apis.IBrokerProxy import IBrokerProxy


class IAuthorityProxy(IBrokerProxy):
    """
    IAuthorityProxy represents the proxy interface to an actor acting in the authority role.
    """
    def prepare_close(self, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                      caller: AuthToken) -> IRPCRequestState:
        raise NotImplementedError("Should have implemented this")

    def prepare_extend_lease(self, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                             caller: AuthToken) -> IRPCRequestState:
        raise NotImplementedError("Should have implemented this")

    def prepare_modify_lease(self, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                             caller: AuthToken) -> IRPCRequestState:
        raise NotImplementedError("Should have implemented this")

    def prepare_redeem(self, reservation: IControllerReservation, callback: IControllerCallbackProxy, caller:
    AuthToken) -> IRPCRequestState:
        raise NotImplementedError("Should have implemented this")