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
import threading

from fabric_cf.actor.core.apis.i_actor import IActor
from fabric_cf.actor.core.apis.i_actor_proxy import IActorProxy
from fabric_cf.actor.core.apis.i_authority_proxy import IAuthorityProxy
from fabric_cf.actor.core.apis.i_authority_reservation import IAuthorityReservation
from fabric_cf.actor.core.apis.i_broker_proxy import IBrokerProxy
from fabric_cf.actor.core.apis.i_broker_reservation import IBrokerReservation
from fabric_cf.actor.core.apis.i_callback_proxy import ICallbackProxy
from fabric_cf.actor.core.apis.i_client_callback_proxy import IClientCallbackProxy
from fabric_cf.actor.core.apis.i_client_reservation import IClientReservation
from fabric_cf.actor.core.apis.i_controller_callback_proxy import IControllerCallbackProxy
from fabric_cf.actor.core.apis.i_controller_reservation import IControllerReservation
from fabric_cf.actor.core.apis.i_delegation import IDelegation
from fabric_cf.actor.core.apis.i_query_response_handler import IQueryResponseHandler
from fabric_cf.actor.core.apis.i_reservation import IReservation
from fabric_cf.actor.core.common.constants import Constants
from fabric_cf.actor.core.kernel.claim_timeout import ClaimTimeout, ReclaimTimeout
from fabric_cf.actor.core.kernel.failed_rpc import FailedRPC
from fabric_cf.actor.core.kernel.failed_rpc_event import FailedRPCEvent
from fabric_cf.actor.core.kernel.inbound_rpc_event import InboundRPCEvent
from fabric_cf.actor.core.kernel.incoming_failed_rpc import IncomingFailedRPC
from fabric_cf.actor.core.kernel.incoming_rpc import IncomingRPC
from fabric_cf.actor.core.kernel.incoming_rpc_event import IncomingRPCEvent
from fabric_cf.actor.core.kernel.incoming_reservation_rpc import IncomingReservationRPC
from fabric_cf.actor.core.kernel.outbound_rpc_event import OutboundRPCEvent
from fabric_cf.actor.core.kernel.query_timeout import QueryTimeout
from fabric_cf.actor.core.kernel.rpc_executor import RPCExecutor
from fabric_cf.actor.core.kernel.rpc_request import RPCRequest
from fabric_cf.actor.core.kernel.rpc_request_type import RPCRequestType
from fabric_cf.actor.core.proxies.proxy import Proxy
from fabric_cf.actor.core.util.kernel_timer import KernelTimer
from fabric_cf.actor.core.util.rpc_exception import RPCException, RPCError
from fabric_cf.actor.core.util.update_data import UpdateData
from fabric_cf.actor.security.auth_token import AuthToken


class RPCManager:
    """
    Class responsible for message exchange across Kafka
    """
    CLAIM_TIMEOUT_SECONDS = 120
    QUERY_TIMEOUT_SECONDS = 120

    def __init__(self):
        # Table of pending RPC requests.
        self.pending = {}
        self.started = False
        self.num_queued = 0
        self.pending_lock = threading.Lock()
        self.stats_lock = threading.Condition()

    @staticmethod
    def validate_delegation(*, delegation: IDelegation, check_requested: bool = False):
        if delegation is None:
            raise RPCException(message=Constants.not_specified_prefix.format("delegation"))

        if delegation.get_slice_object() is None:
            raise RPCException(message=Constants.not_specified_prefix.format("slice"))

        if check_requested and delegation.get_graph() is None:
            raise RPCException(message=Constants.not_specified_prefix.format("graph"))

    @staticmethod
    def validate(*, reservation: IReservation, check_requested: bool = False):
        if reservation is None:
            raise RPCException(message=Constants.not_specified_prefix.format("reservation"))

        if reservation.get_slice() is None:
            raise RPCException(message=Constants.not_specified_prefix.format("slice"))

        if check_requested:
            if reservation.get_requested_resources() is None:
                raise RPCException(message=Constants.not_specified_prefix.format("requested resources"))

            if reservation.get_requested_term() is None:
                raise RPCException(message=Constants.not_specified_prefix.format("requested term"))

        if isinstance(reservation, IClientReservation):
            if reservation.get_broker() is None:
                raise RPCException(message=Constants.not_specified_prefix.format("broker proxy"))

            if reservation.get_client_callback_proxy() is None:
                raise RPCException(message=Constants.not_specified_prefix.format("client callback proxy"))

        elif isinstance(reservation, IControllerReservation):
            if reservation.get_authority() is None:
                raise RPCException(message=Constants.not_specified_prefix.format("authority proxy"))

            if reservation.get_client_callback_proxy() is None:
                raise RPCException(message=Constants.not_specified_prefix.format("client callback proxy"))

    def start(self):
        self.do_start()

    def stop(self):
        self.do_stop()

    def retry(self, *, request: RPCRequest):
        if request is None:
            raise RPCException(message=Constants.not_specified_prefix.format("request"))
        self.do_retry(rpc=request)

    def failed_rpc(self, *, actor: IActor, rpc: IncomingRPC, e: Exception):
        if actor is None:
            raise RPCException(message=Constants.not_specified_prefix.format("actor"))

        if rpc is None:
            raise RPCException(message=Constants.not_specified_prefix.format("rpc"))

        if rpc.get_callback() is None:
            raise RPCException(message=Constants.not_specified_prefix.format("callback"))

        if isinstance(rpc, IncomingFailedRPC):
            raise RPCException(message="Cannot reply to a FailedRPC with a FailedRPC")

        self.do_failed_rpc(actor=actor, proxy=rpc.get_callback(), rpc=rpc, e=e, caller=actor.get_identity())

    def claim_delegation(self, *, delegation: IDelegation, id_token: str = None):
        self.validate_delegation(delegation=delegation)
        self.do_claim_delegation(actor=delegation.get_actor(), proxy=delegation.get_broker(),
                                 delegation=delegation, callback=delegation.get_client_callback_proxy(),
                                 caller=delegation.get_slice_object().get_owner(), id_token=id_token)

    def reclaim_delegation(self, *, delegation: IDelegation, id_token: str = None):
        self.validate_delegation(delegation=delegation)
        self.do_reclaim_delegation(actor=delegation.get_actor(), proxy=delegation.get_broker(),
                                   delegation=delegation, callback=delegation.get_client_callback_proxy(),
                                   caller=delegation.get_slice_object().get_owner(), id_token=id_token)

    def ticket(self, *, reservation: IClientReservation):
        self.validate(reservation=reservation, check_requested=True)
        self.do_ticket(actor=reservation.get_actor(), proxy=reservation.get_broker(),
                       reservation=reservation, callback=reservation.get_client_callback_proxy(),
                       caller=reservation.get_slice().get_owner())

    def extend_ticket(self, *, reservation: IClientReservation):
        self.validate(reservation=reservation, check_requested=True)
        self.do_extend_ticket(actor=reservation.get_actor(), proxy=reservation.get_broker(),
                              reservation=reservation, callback=reservation.get_client_callback_proxy(),
                              caller=reservation.get_slice().get_owner())

    def relinquish(self, *, reservation: IClientReservation):
        self.validate(reservation=reservation)
        self.do_relinquish(actor=reservation.get_actor(), proxy=reservation.get_broker(),
                           reservation=reservation, callback=reservation.get_client_callback_proxy(),
                           caller=reservation.get_slice().get_owner())

    def redeem(self, *, reservation: IControllerReservation):
        self.validate(reservation=reservation, check_requested=True)
        self.do_redeem(actor=reservation.get_actor(), proxy=reservation.get_authority(),
                       reservation=reservation, callback=reservation.get_client_callback_proxy(),
                       caller=reservation.get_slice().get_owner())

    def extend_lease(self, *, proxy: IAuthorityProxy, reservation: IControllerReservation, caller: AuthToken):
        self.validate(reservation=reservation, check_requested=True)
        self.do_extend_lease(actor=reservation.get_actor(), proxy=reservation.get_authority(),
                             reservation=reservation, callback=reservation.get_client_callback_proxy(),
                             caller=reservation.get_slice().get_owner())

    def modify_lease(self, *, proxy: IAuthorityProxy, reservation: IControllerReservation, caller: AuthToken):
        self.validate(reservation=reservation, check_requested=True)
        self.do_modify_lease(actor=reservation.get_actor(), proxy=reservation.get_authority(),
                             reservation=reservation, callback=reservation.get_client_callback_proxy(),
                             caller=reservation.get_slice().get_owner())

    def close(self, *, reservation: IControllerReservation):
        self.validate(reservation=reservation)
        self.do_close(actor=reservation.get_actor(), proxy=reservation.get_authority(),
                      reservation=reservation, callback=reservation.get_client_callback_proxy(),
                      caller=reservation.get_slice().get_owner())

    def update_ticket(self, *, reservation: IBrokerReservation):
        self.validate(reservation=reservation)
        # get a callback to the actor calling updateTicket, so that any
        # failures in the remote actor can be delivered back
        callback = Proxy.get_callback(actor=reservation.get_actor(), protocol=reservation.get_callback().get_type())
        if callback is None:
            raise RPCException(message=Constants.not_specified_prefix.format("callback"))
        self.do_update_ticket(actor=reservation.get_actor(), proxy=reservation.get_callback(),
                              reservation=reservation, update_data=reservation.get_update_data(),
                              callback=callback, caller=reservation.get_actor().get_identity())

    def update_delegation(self, *, delegation: IDelegation):
        self.validate_delegation(delegation=delegation, check_requested=True)
        # get a callback to the actor calling updateTicket, so that any
        # failures in the remote actor can be delivered back
        callback = Proxy.get_callback(actor=delegation.get_actor(), protocol=delegation.get_callback().get_type())
        if callback is None:
            raise RPCException(message=Constants.not_specified_prefix.format("callback"))
        self.do_update_delegation(actor=delegation.get_actor(), proxy=delegation.get_callback(),
                                  delegation=delegation, update_data=delegation.get_update_data(),
                                  callback=callback, caller=delegation.get_actor().get_identity())

    def update_lease(self, *, reservation: IAuthorityReservation):
        self.validate(reservation=reservation)
        # get a callback to the actor calling updateTicket, so that any
        # failures in the remote actor can be delivered back
        callback = Proxy.get_callback(actor=reservation.get_actor(), protocol=reservation.get_callback().get_type())
        if callback is None:
            raise RPCException(message=Constants.not_specified_prefix.format("callback"))
        self.do_update_lease(actor=reservation.get_actor(), proxy=reservation.get_callback(),
                             reservation=reservation, update_data=reservation.get_update_data(),
                             callback=callback, caller=reservation.get_actor().get_identity())

    def query(self, *, actor: IActor, remote_actor: IActorProxy, callback: ICallbackProxy,
              query: dict, handler: IQueryResponseHandler, id_token: str):
        if actor is None:
            raise RPCException(message=Constants.not_specified_prefix.format("actor"))
        if remote_actor is None:
            raise RPCException(message=Constants.not_specified_prefix.format("remote actor"))
        if callback is None:
            raise RPCException(message=Constants.not_specified_prefix.format("callback"))
        if query is None:
            raise RPCException(message=Constants.not_specified_prefix.format("query"))
        if handler is None:
            raise RPCException(message=Constants.not_specified_prefix.format("handler"))
        self.do_query(actor=actor, remote_actor=remote_actor, local_actor=callback, query=query,
                      handler=handler, caller=callback.get_identity(), id_token=id_token)

    def query_result(self, *, actor: IActor, remote_actor: ICallbackProxy, request_id: str, response: dict,
                     caller: AuthToken):
        if actor is None:
            raise RPCException(message=Constants.not_specified_prefix.format("actor"))
        if remote_actor is None:
            raise RPCException(message=Constants.not_specified_prefix.format("remote actor"))
        if request_id is None:
            raise RPCException(message=Constants.not_specified_prefix.format("request id"))
        if response is None:
            raise RPCException(message=Constants.not_specified_prefix.format("response"))
        if caller is None:
            raise RPCException(message=Constants.not_specified_prefix.format("caller"))
        self.do_query_result(actor=actor, remote_actor=remote_actor, request_id=request_id, response=response,
                             caller=caller)

    def dispatch_incoming(self, *, actor: IActor, rpc: IncomingRPC):
        if actor is None:
            raise RPCException(message=Constants.not_specified_prefix.format("actor"))
        if rpc is None:
            raise RPCException(message=Constants.not_specified_prefix.format("rpc"))
        self.do_dispatch_incoming_rpc(actor=actor, rpc=rpc)

    def await_nothing_pending(self):
        self.do_await_nothing_pending()

    def do_await_nothing_pending(self):
        with self.stats_lock:
            while self.num_queued > 0:
                self.stats_lock.wait()

    def do_start(self):
        try:
            self.pending_lock.acquire()
            self.pending.clear()
        finally:
            self.pending_lock.release()
        self.started = True

    def do_stop(self):
        self.started = False
        try:
            self.pending_lock.acquire()
            self.pending.clear()
        finally:
            self.pending_lock.release()

    def do_failed_rpc(self, *, actor: IActor, proxy: ICallbackProxy, rpc: IncomingRPC, e: Exception, caller: AuthToken):
        proxy.get_logger().info("Outbound failedRPC request from <{}>: requestID={}".format(caller.get_name(),
                                                                                            rpc.get_message_id()))
        message = "RPC failed at remote actor."
        if e is not None:
            message += " message:{}".format(e)

        rid = None
        if isinstance(rpc, IncomingReservationRPC):
            rid = rpc.get_reservation().get_reservation_id()

        state = proxy.prepare_failed_request(request_id=str(rpc.get_message_id()),
                                             failed_request_type=rpc.get_request_type(),
                                             failed_reservation_id=rid, error=message, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.FailedRPC)
        outgoing = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=None, sequence=0)
        self.enqueue(rpc=outgoing)

    def do_claim_delegation(self, *, actor: IActor, proxy: IBrokerProxy, delegation: IDelegation,
                            callback: IClientCallbackProxy, caller: AuthToken, id_token: str = None):
        proxy.get_logger().info("Outbound claim delegation request from <{}>: {}".format(caller.get_name(), delegation))

        state = proxy.prepare_claim_delegation(delegation=delegation, callback=callback,
                                               caller=caller, id_token=id_token)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.ClaimDelegation)

        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, delegation=delegation,
                         sequence=delegation.get_sequence_out())
        # Schedule a timeout
        rpc.timer = KernelTimer.schedule(queue=actor, task=ClaimTimeout(req=rpc), delay=self.CLAIM_TIMEOUT_SECONDS)
        self.enqueue(rpc=rpc)

    def do_reclaim_delegation(self, *, actor: IActor, proxy: IBrokerProxy, delegation: IDelegation,
                              callback: IClientCallbackProxy, caller: AuthToken, id_token: str = None):
        proxy.get_logger().info("Outbound reclaim delegation request from <{}>: {}".format(
            caller.get_name(), delegation))

        state = proxy.prepare_reclaim_delegation(delegation=delegation, callback=callback,
                                                 caller=caller, id_token=id_token)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.ReclaimDelegation)

        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, delegation=delegation,
                         sequence=delegation.get_sequence_out())
        # Schedule a timeout
        rpc.timer = KernelTimer.schedule(queue=actor, task=ReclaimTimeout(req=rpc), delay=self.CLAIM_TIMEOUT_SECONDS)
        self.enqueue(rpc=rpc)

    def do_ticket(self, *, actor: IActor, proxy: IBrokerProxy, reservation: IClientReservation,
                  callback: IClientCallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound ticket request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_ticket(reservation=reservation, callback=callback, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.Ticket)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_ticket_sequence_out())
        self.enqueue(rpc=rpc)

    def do_extend_ticket(self, *, actor: IActor, proxy: IBrokerProxy, reservation: IClientReservation,
                         callback: IClientCallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound extend ticket request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_extend_ticket(reservation=reservation, callback=callback, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.ExtendTicket)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_ticket_sequence_out())
        self.enqueue(rpc=rpc)

    def do_relinquish(self, *, actor: IActor, proxy: IBrokerProxy, reservation: IClientReservation,
                      callback: IClientCallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound relinquish request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_relinquish(reservation=reservation, callback=callback, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.Relinquish)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_ticket_sequence_out())
        self.enqueue(rpc=rpc)

    def do_redeem(self, *, actor: IActor, proxy: IAuthorityProxy, reservation: IControllerReservation,
                  callback: IControllerCallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound relinquish redeem from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_redeem(reservation=reservation, callback=callback, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.Redeem)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_ticket_sequence_out())
        self.enqueue(rpc=rpc)

    def do_extend_lease(self, *, actor: IActor, proxy: IAuthorityProxy, reservation: IControllerReservation,
                        callback: IControllerCallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound extend lease request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_extend_lease(reservation=reservation, callback=callback, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.ExtendLease)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_lease_sequence_out())
        self.enqueue(rpc=rpc)

    def do_modify_lease(self, *, actor: IActor, proxy: IAuthorityProxy, reservation: IControllerReservation,
                        callback: IControllerCallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound modify lease request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_modify_lease(reservation=reservation, callback=callback, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.ModifyLease)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_lease_sequence_out())
        self.enqueue(rpc=rpc)

    def do_close(self, *, actor: IActor, proxy: IAuthorityProxy, reservation: IControllerReservation,
                 callback: IControllerCallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound close request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_close(reservation=reservation, callback=callback, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.Close)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_lease_sequence_out())
        self.enqueue(rpc=rpc)

    def do_update_ticket(self, *, actor: IActor, proxy: IClientCallbackProxy, reservation: IBrokerReservation,
                         update_data: UpdateData, callback: ICallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound update ticket request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_update_ticket(reservation=reservation, update_data=update_data, callback=callback,
                                            caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.UpdateTicket)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_sequence_out())
        self.enqueue(rpc=rpc)

    def do_update_delegation(self, *, actor: IActor, proxy: IClientCallbackProxy, delegation: IDelegation,
                             update_data: UpdateData, callback: ICallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound update delegation request from <{}>: {}".format(
            caller.get_name(), delegation))

        state = proxy.prepare_update_delegation(delegation=delegation, update_data=update_data, callback=callback,
                                                caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.UpdateDelegation)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, delegation=delegation,
                         sequence=delegation.get_sequence_out())
        self.enqueue(rpc=rpc)

    def do_update_lease(self, *, actor: IActor, proxy: IControllerCallbackProxy, reservation: IAuthorityReservation,
                        update_data: UpdateData, callback: ICallbackProxy, caller: AuthToken):
        proxy.get_logger().info("Outbound update lease request from <{}>: {}".format(caller.get_name(), reservation))

        state = proxy.prepare_update_lease(reservation=reservation, update_data=update_data, callback=callback,
                                           caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.UpdateLease)
        rpc = RPCRequest(request=state, actor=actor, proxy=proxy, reservation=reservation,
                         sequence=reservation.get_sequence_out())
        self.enqueue(rpc=rpc)

    def do_query(self, *, actor: IActor, remote_actor: IActorProxy, local_actor: ICallbackProxy,
                 query: dict, handler: IQueryResponseHandler, caller: AuthToken, id_token: str):
        remote_actor.get_logger().info("Outbound query request from <{}>".format(caller.get_name()))

        state = remote_actor.prepare_query(callback=local_actor, query=query, caller=caller, id_token=id_token)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.Query)
        rpc = RPCRequest(request=state, actor=actor, proxy=remote_actor, handler=handler)
        # Timer
        rpc.timer = KernelTimer.schedule(queue=actor, task=QueryTimeout(req=rpc), delay=self.QUERY_TIMEOUT_SECONDS)
        remote_actor.get_logger().info("Timer started: {}".format(rpc.timer))
        self.enqueue(rpc=rpc)

    def do_query_result(self, *, actor: IActor, remote_actor: ICallbackProxy, request_id: str,
                        response: dict, caller: AuthToken):
        remote_actor.get_logger().info("Outbound query_result request from <{}>".format(caller.get_name()))

        state = remote_actor.prepare_query_result(request_id=request_id, response=response, caller=caller)
        state.set_caller(caller=caller)
        state.set_type(rtype=RPCRequestType.QueryResult)
        rpc = RPCRequest(request=state, actor=actor, proxy=remote_actor)
        self.enqueue(rpc=rpc)

    def do_dispatch_incoming_rpc(self, *, actor: IActor, rpc: IncomingRPC):
        # see if this is a response for an earlier request that has an
        # associated handler function. If a handler exists, attach the handler
        # to the incoming rpc object.
        request = None
        if rpc.get_request_id() is not None:
            request = self.remove_pending_request(guid=rpc.get_request_id())
            if request is not None:
                if request.timer:
                    actor.get_logger().debug("Canceling the timer: {}".format(request.timer))
                request.cancel_timer()
                if request.handler is not None:
                    rpc.set_response_handler(response_handler=request.handler)

        if rpc.get_request_type() == RPCRequestType.Query:
            actor.get_logger().info("Inbound query from <{}>".format(rpc.get_caller().get_name()))

        elif rpc.get_request_type() == RPCRequestType.QueryResult:
            actor.get_logger().info("Inbound query response from <{}>".format(rpc.get_caller().get_name()))

            if request is None:
                actor.get_logger().warning("No queryRequest to match to inbound queryResponse. Ignoring response")

        elif rpc.get_request_type() == RPCRequestType.ClaimDelegation:
            actor.get_logger().info("Inbound claim delegation request from <{}>:{}".format(
                rpc.get_caller().get_name(), rpc.get_delegation()))

        elif rpc.get_request_type() == RPCRequestType.ReclaimDelegation:
            actor.get_logger().info("Inbound reclaim delegation request from <{}>:{}".format(
                rpc.get_caller().get_name(), rpc.get_delegation()))

        elif rpc.get_request_type() == RPCRequestType.Ticket:
            actor.get_logger().info("Inbound ticket request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                 rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.ExtendTicket:
            actor.get_logger().info("Inbound extend ticket request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                        rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.Relinquish:
            actor.get_logger().info("Inbound relinquish request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                     rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.UpdateTicket:
            actor.get_logger().info("Inbound update ticket request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                        rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.UpdateDelegation:
            actor.get_logger().info("Inbound update delegation request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                            rpc.get_delegation()))

        elif rpc.get_request_type() == RPCRequestType.Redeem:
            actor.get_logger().info("Inbound redeem request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                 rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.ExtendLease:
            actor.get_logger().info("Inbound extend lease request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                       rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.Close:
            actor.get_logger().info("Inbound close request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.UpdateLease:
            actor.get_logger().info("Inbound update lease request from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                                       rpc.get_reservation()))

        elif rpc.get_request_type() == RPCRequestType.FailedRPC:
            actor.get_logger().info("Inbound FailedRPC from <{}>:{}".format(rpc.get_caller().get_name(),
                                                                            rpc.get_reservation()))

        if rpc.get_request_type() == RPCRequestType.FailedRPC:
            actor.get_logger().debug("Failed RPC")
            failed = None
            exception = RPCException(message=rpc.get_error_details(), error=RPCError.RemoteError)
            if request is not None:
                if request.proxy.get_identity() == rpc.get_caller():
                    failed = FailedRPC(e=exception, request=request)
                else:
                    actor.get_logger().warning("Failed RPC from an unauthorized caller: expected={} but was={}".format(
                        request.proxy.get_identity(), rpc.get_caller()))

            elif rpc.get_failed_reservation_id() is not None:
                failed = FailedRPC(e=exception, request_type=rpc.get_failed_request_type(),
                                   rid=rpc.get_failed_reservation_id(), auth=rpc.caller)
            else:
                failed = FailedRPC(e=exception, request_type=rpc.get_failed_request_type(), auth=rpc.caller)

            if failed is not None:
                actor.queue_event(incoming=FailedRPCEvent(actor=actor, failed=failed))

        else:
            actor.get_logger().debug("Added to actor queue to be processed")
            from fabric_cf.actor.core.container.globals import GlobalsSingleton
            GlobalsSingleton.get().event_manager.dispatch_event(event=InboundRPCEvent(request=rpc, actor=actor))
            actor.queue_event(incoming=IncomingRPCEvent(actor=actor, rpc=rpc))

    def do_retry(self, *, rpc: RPCRequest):
        rpc.retry_count += 1
        from fabric_cf.actor.core.container.globals import GlobalsSingleton
        logger = GlobalsSingleton.get().get_logger()
        logger.debug("Retrying RPC({}) count={} actor={}".format(rpc.get_request_type(), rpc.retry_count,
                                                                 rpc.get_actor().get_name()))
        self.enqueue(rpc=rpc)

    def add_pending_request(self, *, guid: str, request: RPCRequest):
        try:
            self.pending_lock.acquire()
            from fabric_cf.actor.core.container.globals import GlobalsSingleton
            logger = GlobalsSingleton.get().get_logger()
            logger.debug("Added request with rid: {}".format(guid))
            self.pending[guid] = request
            logger.debug("Pending Queue: {}".format(self.pending))
        finally:
            self.pending_lock.release()

    def remove_pending_request(self, *, guid: str) -> RPCRequest:
        result = None
        try:
            self.pending_lock.acquire()
            from fabric_cf.actor.core.container.globals import GlobalsSingleton
            logger = GlobalsSingleton.get().get_logger()
            logger.debug("Removing request with rid: {}".format(guid))
            logger.debug("Pending Queue: {}".format(self.pending))
            if guid in self.pending:
                result = self.pending.pop(guid)
        finally:
            self.pending_lock.release()
        return result

    def queued(self):
        with self.stats_lock:
            self.num_queued += 1
            print("Queued: {}".format(self.num_queued))

    def de_queued(self):
        with self.stats_lock:
            if self.num_queued == 0:
                raise RPCException(message="De-queued invoked, but nothing is queued!!!")

            self.num_queued -= 1
            print("DeQueued: {}".format(self.num_queued))
            if self.num_queued == 0:
                self.stats_lock.notify_all()

    def enqueue(self, *, rpc: RPCRequest):
        if not self.started:
            print("Ignoring RPC request: container is shutting down")
            return
        if rpc.handler is not None:
            self.add_pending_request(guid=rpc.request.get_message_id(), request=rpc)

        from fabric_cf.actor.core.container.globals import GlobalsSingleton
        GlobalsSingleton.get().event_manager.dispatch_event(event=OutboundRPCEvent(request=rpc))

        try:
            self.queued()
            rpc_executor = RPCExecutor(request=rpc)
            # TODO Thread Pool
            thread = threading.Thread(target=rpc_executor.run())
            thread.setName("RPCExecutor {}".format(rpc.request.get_message_id()))
            thread.start()
        except Exception as e:
            print("Exception occurred while starting RPC Executor {}".format(e))
            self.de_queued()
            if rpc.handler is not None:
                self.remove_pending_request(guid=rpc.request.get_message_id())
            raise e
