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
from fabric_cf.actor.core.apis.i_authority_proxy import IAuthorityProxy
from fabric_cf.actor.core.apis.i_controller_callback_proxy import IControllerCallbackProxy
from fabric_cf.actor.core.apis.i_controller_reservation import IControllerReservation
from fabric_cf.actor.core.apis.i_rpc_request_state import IRPCRequestState
from fabric_cf.actor.core.apis.i_reservation import IReservation
from fabric_cf.actor.core.common.constants import Constants
from fabric_cf.actor.core.common.exceptions import ProxyException
from fabric_cf.actor.core.kernel.authority_reservation_factory import AuthorityReservationFactory
from fabric_cf.actor.core.proxies.local.local_broker import LocalBroker
from fabric_cf.actor.core.proxies.local.local_proxy import LocalProxy
from fabric_cf.actor.core.util.resource_data import ResourceData
from fabric_cf.actor.security.auth_token import AuthToken


class LocalAuthority(LocalBroker, IAuthorityProxy):
    def _prepare(self, *, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                 caller: AuthToken) -> IRPCRequestState:
        state = LocalProxy.LocalProxyRequestState()
        state.reservation = self.pass_reservation_authority(reservation=reservation, auth=caller)
        state.callback = callback
        return state

    def prepare_redeem(self, *, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                       caller: AuthToken) -> IRPCRequestState:
        return self._prepare(reservation=reservation, callback=callback, caller=caller)

    def prepare_extend_lease(self, *, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                             caller: AuthToken) -> IRPCRequestState:
        return self._prepare(reservation=reservation, callback=callback, caller=caller)

    def prepare_modify_lease(self, *, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                             caller: AuthToken) -> IRPCRequestState:
        return self._prepare(reservation=reservation, callback=callback, caller=caller)

    def prepare_close(self, *, reservation: IControllerReservation, callback: IControllerCallbackProxy,
                      caller: AuthToken) -> IRPCRequestState:
        return self._prepare(reservation=reservation, callback=callback, caller=caller)

    def pass_reservation_authority(self, *, reservation: IControllerReservation, auth: AuthToken) -> IReservation:
        if reservation.get_resources().get_resources() is None:
            raise ProxyException(Constants.not_specified_prefix.format("concrete set"))

        slice_obj = reservation.get_slice().clone_request()
        term = reservation.get_term().clone()

        rset = self.abstract_clone_authority(rset=reservation.get_resources())
        rset.get_resource_data().configuration_properties = ResourceData.merge_properties(
            from_props=reservation.get_slice().get_config_properties(),
            to_props=rset.get_resource_data().get_configuration_properties())

        original_ticket = reservation.get_resources().get_resources()
        encoded_ticket = original_ticket.encode(protocol=Constants.protocol_local)
        from fabric_cf.actor.core.proxies.proxy import Proxy
        decoded_ticket = Proxy.decode(encoded=encoded_ticket, plugin=self.get_actor().get_plugin())
        rset.set_resources(cset=decoded_ticket)

        authority_reservation = AuthorityReservationFactory.create(resources=rset, term=term, slice_obj=slice_obj,
                                                                   rid=reservation.get_reservation_id())
        authority_reservation.set_sequence_in(sequence=reservation.get_lease_sequence_out())
        authority_reservation.set_owner(owner=self.get_identity())

        return authority_reservation
