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
from fabric.actor.core.apis.IAuthorityReservation import IAuthorityReservation
from fabric.actor.core.apis.ICallbackProxy import ICallbackProxy
from fabric.actor.core.apis.IControllerCallbackProxy import IControllerCallbackProxy
from fabric.actor.core.apis.IRPCRequestState import IRPCRequestState
from fabric.actor.core.apis.IReservation import IReservation
from fabric.actor.core.common.Constants import Constants
from fabric.actor.core.kernel.RPCRequestType import RPCRequestType
from fabric.actor.core.proxies.local.LocalReturn import LocalReturn
from fabric.actor.core.registry.ActorRegistry import ActorRegistrySingleton
from fabric.actor.core.util.ID import ID
from fabric.actor.core.util.UpdateData import UpdateData
from fabric.actor.security.AuthToken import AuthToken
from fabric.actor.test.ClientCallbackHelper import ClientCallbackHelper


class ControllerCallbackHelper(ClientCallbackHelper, IControllerCallbackProxy):
    class IUpdateLeaseHandler:
        def handle_update_lease(self, reservation: IReservation, update_data: UpdateData, caller: AuthToken):
            pass

        def check_termination(self):
            pass

    def __init__(self, name: str, guid: ID):
        super().__init__(name, guid)
        self.called_for_lease = 0
        self.lease = None
        self.updateLeaseHandler = None

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['updateLeaseHandler']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.updateLeaseHandler = None

    def prepare_update_lease(self, reservation: IAuthorityReservation, update_data: UpdateData,
                             callback: ICallbackProxy, caller: AuthToken) -> IRPCRequestState:
        state = ClientCallbackHelper.MyRequestState()
        state.reservation = LocalReturn.pass_reservation(reservation,
                                                         ActorRegistrySingleton.get().get_actor(
                                                             self.token.get_name()).get_plugin())
        state.update_data = UpdateData()
        state.update_data.absorb(update_data)
        return state

    def execute(self, request: IRPCRequestState):
        if request.get_type() == RPCRequestType.UpdateLease:
            self.lease = request.reservation
            self.called_for_lease += 1
            if self.updateLeaseHandler is not None:
                self.updateLeaseHandler.handle_update_lease(self.lease, request.update_data, request.get_caller())
            else:
                super().execute(request)

    def get_lease(self) -> IReservation:
        return self.lease

    def get_called_for_lease(self):
        return self.called_for_lease

    def set_update_lease_handler(self, handler: IUpdateLeaseHandler):
        self.updateLeaseHandler = handler

    def get_called(self) -> int:
        return self.called

    def get_guid(self) -> ID:
        return self.token.get_guid()

    def get_identity(self) -> AuthToken:
        return self.token

    def get_name(self) -> str:
        return self.token.get_name()

    def get_reservation(self) -> IReservation:
        return self.reservation

    def get_type(self):
        return Constants.ProtocolLocal

    def prepare_query_result(self, request_id: str, response, caller: AuthToken) -> IRPCRequestState:
        raise Exception("Not implemented")

    def prepare_failed_request(self, request_id: str, failed_request_type,
                               failed_reservation_id: ID, error: str, caller: AuthToken) -> IRPCRequestState:
        raise ("Not implemented")