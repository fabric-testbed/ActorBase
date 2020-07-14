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
from fabric.actor.core.apis.IActor import IActor
from fabric.actor.core.apis.IAuthorityProxy import IAuthorityProxy
from fabric.actor.core.apis.IControllerCallbackProxy import IControllerCallbackProxy
from fabric.actor.core.apis.IControllerReservation import IControllerReservation
from fabric.actor.core.apis.IRPCRequestState import IRPCRequestState
from fabric.actor.core.apis.IReservation import IReservation
from fabric.actor.core.common.Constants import Constants
from fabric.actor.core.kernel.AuthorityReservationFactory import AuthorityReservationFactory
from fabric.actor.core.proxies.local.LocalBroker import LocalBroker
from fabric.actor.core.proxies.local.LocalProxy import LocalProxy
from fabric.actor.core.util.ResourceData import ResourceData
from fabric.actor.security.AuthToken import AuthToken


class LocalAuthority(LocalBroker, IAuthorityProxy):
    def __init__(self, actor: IActor):
        super().__init__(actor)

    def prepare_redeem(self, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                       caller: AuthToken) -> IRPCRequestState:
        state = LocalProxy.LocalProxyRequestState()
        state.reservation = self.pass_reservation_authority(reservation, caller)
        state.callback = callback
        return state

    def prepare_extend_lease(self, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                             caller: AuthToken) -> IRPCRequestState:
        state = LocalProxy.LocalProxyRequestState()
        state.reservation = self.pass_reservation_authority(reservation, caller)
        state.callback = callback
        return state

    def prepare_modify_lease(self, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                             caller: AuthToken) -> IRPCRequestState:
        state = LocalProxy.LocalProxyRequestState()
        state.reservation = self.pass_reservation_authority(reservation, caller)
        state.callback = callback
        return state

    def prepare_close(self, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                      caller: AuthToken) -> IRPCRequestState:
        state = LocalProxy.LocalProxyRequestState()
        state.reservation = self.pass_reservation_authority(reservation, caller)
        state.callback = callback
        return state

    def pass_reservation_authority(self, reservation: IControllerReservation, auth: AuthToken) -> IReservation:
        if reservation.get_resources().get_resources() is None:
            raise Exception("Missing ticket")

        slice_obj = reservation.get_slice().clone_request()
        term = reservation.get_term().clone()

        rset = self.abstract_clone_authority(reservation.get_resources())
        rset.get_resource_data().configuration_properties = ResourceData.merge_properties(
            reservation.get_slice().get_config_properties(), rset.get_resource_data().get_configuration_properties())

        original_ticket = reservation.get_resources().get_resources()
        try:
            encoded_ticket = original_ticket.encode(Constants.ProtocolLocal)
            from fabric.actor.core.proxies.Proxy import Proxy
            decoded_ticket = Proxy.decode(encoded_ticket, self.get_actor().get_plugin())
            rset.set_resources(decoded_ticket)
        except Exception as e:
            raise e

        authority_reservation = AuthorityReservationFactory.create(rset, term, slice_obj, reservation.get_reservation_id())
        authority_reservation.set_sequence_in(reservation.get_lease_sequence_out())
        authority_reservation.set_owner(self.get_identity())

        return authority_reservation