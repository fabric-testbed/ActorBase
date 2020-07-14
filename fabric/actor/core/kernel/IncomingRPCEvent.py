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

from fabric.actor.core.kernel.RPCRequestType import RPCRequestType

if TYPE_CHECKING:

    from fabric.actor.core.apis.IActor import IActor
    from fabric.actor.core.kernel.IncomingRPC import IncomingRPC
    from fabric.actor.core.apis.IClientActor import IClientActor
    from fabric.actor.core.apis.IServerActor import IServerActor

from fabric.actor.core.apis.IActorEvent import IActorEvent
from fabric.actor.core.apis.IAuthority import IAuthority
from fabric.actor.core.apis.IBroker import IBroker
from fabric.actor.core.apis.IController import IController


class IncomingRPCEvent(IActorEvent):
    def __init__(self, actor: IActor, rpc: IncomingRPC):
        self.actor = actor
        self.rpc = rpc

    def do_process_actor(self, actor: IActor):
        processed = True
        if self.rpc.get_request_type() == RPCRequestType.Query:
            actor.get_logger().info("processing query from <{}>".format(self.rpc.get_calller().get_name()))
            result = actor.query(self.rpc.get(), self.rpc.get_caller())
            from fabric.actor.core.kernel.RPCManagerSingleton import RPCManagerSingleton
            RPCManagerSingleton.get().query_result(actor, self.rpc.get_callback(), self.rpc.get_message_id(),
                                                   result, actor.get_identity())
        elif self.rpc.get_request_type() == RPCRequestType.QueryResult:
            actor.get_logger().info("processing query response from <{}>".format(self.rpc.get_calller().get_name()))
            result = self.rpc.get()
            if self.rpc.get_response_handler() is not None:
                handler = self.rpc.get_response_handler()
                handler.handle(self.rpc.get_error(), result)
            else:
                actor.get_logger().warning("No response handler is associated with the queryResponse. Ignoring queryResponse")
        else:
            processed = False
        return processed

    def do_process_client(self, client: IClientActor):
        processed = True
        if self.rpc.get_request_type() == RPCRequestType.UpdateTicket:
            client.get_logger().info("processing update ticket from <{}>".format(self.rpc.get_caller().get_name()))
            client.update_ticket(self.rpc.get_reservation(), self.rpc.get_update_data(), self.rpc.get_caller())
            client.get_logger().info("update ticket processed from <{}>".format(self.rpc.get_caller().get_name()))
        else:
            processed = self.do_process_actor(client)
        return processed

    def do_process_server(self, server: IServerActor):
        processed = True
        if self.rpc.get_request_type() == RPCRequestType.Claim:
            server.get_logger().info("processing claim from <{}>".format(self.rpc.get_caller().get_name()))
            server.claim(self.rpc.get_reservation(), self.rpc.get_callback(), self.rpc.get_caller())
            server.get_logger().info("claim processed from <{}>".format(self.rpc.get_caller().get_name()))

        elif self.rpc.get_request_type() == RPCRequestType.Ticket:
            server.get_logger().info("processing ticket from <{}>".format(self.rpc.get_caller().get_name()))
            server.ticket(self.rpc.get_reservation(), self.rpc.get_callback(), self.rpc.get_caller())
            server.get_logger().info("ticket processed from <{}>".format(self.rpc.get_caller().get_name()))

        elif self.rpc.get_request_type() == RPCRequestType.ExtendTicket:
            server.get_logger().info("processing extend ticket from <{}>".format(self.rpc.get_caller().get_name()))
            server.extend_ticket(self.rpc.get_reservation(), self.rpc.get_caller())
            server.get_logger().info("extend processed from <{}>".format(self.rpc.get_caller().get_name()))

        elif self.rpc.get_request_type() == RPCRequestType.Relinquish:
            server.get_logger().info("processing relinquish from <{}>".format(self.rpc.get_caller().get_name()))
            server.relinquish(self.rpc.get_reservation(), self.rpc.get_caller())
            server.get_logger().info("relinquish processed from <{}>".format(self.rpc.get_caller().get_name()))

        else:
            processed = self.do_process_actor(server)
        return processed

    def do_process_broker(self, broker: IBroker):
        processed = self.do_process_server(broker)
        if not processed:
            processed = self.do_process_client(broker)
        return processed

    def do_process_authority(self, authority: IAuthority):
        processed = True
        if self.rpc.get_request_type() == RPCRequestType.Redeem:
            authority.get_logger().info("processing redeem from <{}>".format(self.rpc.get_caller().get_name()))
            authority.redeem(self.rpc.get_reservation(), self.rpc.get_callback(), self.rpc.get_caller())

        elif self.rpc.get_request_type() == RPCRequestType.ExtendLease:
            authority.get_logger().info("processing extend lease from <{}>".format(self.rpc.get_caller().get_name()))
            authority.extend_lease(self.rpc.get_reservation(), self.rpc.get_caller())

        elif self.rpc.get_request_type() == RPCRequestType.ModifyLease:
            authority.get_logger().info("processing modify lease from <{}>".format(self.rpc.get_caller().get_name()))
            authority.modify_lease(self.rpc.get_reservation(), self.rpc.get_caller())

        elif self.rpc.get_request_type() == RPCRequestType.Close:
            authority.get_logger().info("processing close from <{}>".format(self.rpc.get_caller().get_name()))
            authority.relinquish(self.rpc.get_reservation(), self.rpc.get_caller())

        else:
            processed = self.do_process_server(authority)
        return processed

    def do_process_controller(self, controller: IController):
        processed = True
        if self.rpc.get_request_type() == RPCRequestType.UpdateLease:
            controller.get_logger().info("processing redeem from <{}>".format(self.rpc.get_caller().get_name()))
            if self.rpc.get_reservation().get_resources().get_resources() is not None:
                controller.get_logger().info("inbound lease is {}".format(self.rpc.get_reservation().get_resources().get_resources()))

            controller.update_lease(self.rpc.get_reservation(), self.rpc.get_update_data(), self.rpc.get_caller())
        else:
            processed = self.do_process_client(controller)
        return processed

    def process(self):
        done = False
        if isinstance(self.actor, IAuthority):
            done = self.do_process_authority(self.actor)
            if done:
                return

        if isinstance(self.actor, IBroker):
            done = self.do_process_broker(self.actor)
            if done:
                return

        if isinstance(self.actor, IController):
            done = self.do_process_controller(self.actor)
            if done:
                return

        raise Exception("Unsupported RPC request type: {}".format(self.rpc.get_request_type()))
