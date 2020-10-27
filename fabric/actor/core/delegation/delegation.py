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
from fabric.actor.boot.inventory.neo4j_resource_pool_factory import Neo4jResourcePoolFactory
from fabric.actor.core.apis.i_actor import IActor
from fabric.actor.core.apis.i_callback_proxy import ICallbackProxy
from fabric.actor.core.apis.i_delegation import IDelegation, DelegationState
from fabric.actor.core.apis.i_policy import IPolicy
from fabric.actor.core.apis.i_slice import ISlice
from fabric.actor.core.kernel.rpc_manager_singleton import RPCManagerSingleton
from fabric.actor.core.util.id import ID
from fabric.actor.core.util.update_data import UpdateData
from fabric.actor.security.auth_token import AuthToken
from fim.graph.abc_property_graph import ABCPropertyGraph


class Delegation(IDelegation):
    def __init__(self, dlg_graph_id: ID, slice_id: ID):
        self.dlg_graph_id = dlg_graph_id
        self.slice_id = slice_id
        self.state = DelegationState.Nascent
        self.dirty = False
        self.state_transition = False
        self.sequence_in = 0
        self.update_count = 0
        self.sequence_out = 0
        self.update_data = UpdateData()
        self.must_send_update = False
        self.graph = None
        self.actor = None
        self.slice_object = None
        self.logger = None
        self.policy = None
        self.callback = None
        self.error_message = None
        self.owner = None

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['graph']
        del state['actor']
        del state['slice_object']
        del state['logger']
        del state['policy']
        del state['callback']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.graph = None
        self.actor = None
        self.slice_object = None
        self.logger = None
        self.policy = None
        self.callback = None

    def restore(self, actor: IActor, slice_obj: ISlice, logger):
        self.actor = actor
        self.slice_object = slice_obj
        self.logger = logger
        self.graph = Neo4jResourcePoolFactory.get_arm_graph(graph_id=str(self.dlg_graph_id))

    def set_graph(self, graph: ABCPropertyGraph):
        self.graph = graph

    def get_graph(self) -> ABCPropertyGraph:
        return self.graph

    def get_actor(self) -> IActor:
        return self.actor

    def get_delegation_id(self) -> ID:
        return self.dlg_graph_id

    def get_slice_id(self) -> ID:
        return self.slice_id

    def get_slice_object(self) -> ISlice:
        return self.slice_object

    def get_state(self) -> DelegationState:
        return self.state

    def get_state_name(self) -> str:
        return self.state.name

    def set_logger(self, logger):
        self.logger = logger

    def set_slice_object(self, *, slice_object: ISlice):
        self.slice_object = slice_object

    def transition(self, *, prefix: str, state: DelegationState):
        if self.logger is not None:
            self.logger.debug("Delegation #{} {} transition: {} -> {}".format(self.dlg_graph_id, prefix,
                                                                              self.get_state_name(),
                                                                              state.name))

        self.state = state
        self.set_dirty()
        self.state_transition = True

    def clear_notice(self):
        self.update_data.clear()

    def get_notices(self) -> str:
        msg = "Delegation {} (Slice {} ) is in state [{}]".format(self.get_delegation_id(), self.get_slice_id(),
                                                                  DelegationState(self.state).name)
        if self.error_message is not None and self.error_message != "":
            msg += ", err={}".format(self.error_message)

        notices = self.update_data.get_events()
        s = ""
        if notices is not None:
            s += "\n{}".format(notices)

        notices = self.update_data.get_message()
        if notices is not None:
            s += "\n{}".format(notices)

        return s

    def has_uncommitted_transition(self) -> bool:
        return self.state_transition

    def is_dirty(self) -> bool:
        return self.dirty

    def set_dirty(self):
        self.dirty = True

    def clear_dirty(self):
        self.dirty = False

    def set_actor(self, actor: IActor):
        self.actor = actor

    def prepare(self, *, callback: ICallbackProxy, logger):
        self.set_logger(logger=logger)
        self.callback = callback

        # Null callback indicates a locally initiated request to create an
        # exported delegation. Else the request is from a client and must have
        # a client-specified delegation id.

        if self.callback is not None:
            if self.dlg_graph_id is None:
                self.error(err="no delegation ID specified for request")

        self.set_dirty()

    def is_closed(self) -> bool:
        return self.state == DelegationState.Closed

    def error(self, *, err: str):
        self.error_message = err
        if self.logger is not None:
            self.logger.error("error for delegation: {} : {}".format(self, err))
        else:
            print("error for delegation: {} : {}".format(self, err))
        raise Exception("error: {}".format(err))

    def delegate(self, policy: IPolicy):
        # These handlers may need to be slightly more sophisticated, since a
        # client may bid multiple times on a ticket as part of an auction
        # protocol: so we may receive a reserve or extend when there is already
        # a request pending.
        self.incoming_request()

        self.policy = policy
        self.map_and_update(delegated=False)

    def claim(self):
        if self.state == DelegationState.Delegated:
            # We are an agent asked to return a pre-reserved "will call" ticket
            # to a client. Set mustSendUpdate so that the update will be sent
            # on the next probe.
            self.must_send_update = True
        elif self.state == DelegationState.Reclaimed:
            self.transition(prefix="claim", state=DelegationState.Delegated)
            self.must_send_update = True
        else:
            self.error(err="Wrong delegation state for claim")

    def reclaim(self):
        if self.state == DelegationState.Delegated:
            self.policy.reclaim(delegation=self)
            self.must_send_update = True
            self.transition(prefix="reclaimed", state=DelegationState.Reclaimed)
        else:
            self.error(err="Wrong delegation state for reclaim")

    def close(self):
        send_notification = False
        if self.state == DelegationState.Nascent:
            self.logger.warning("Closing a reservation in progress")
            send_notification = True

        if self.state != DelegationState.Closed:
            self.transition(prefix="closed", state=DelegationState.Closed)
            self.policy.close_delegation(delegation=self)

        if send_notification:
            self.update_data.error(message="Closed while advertising delegation")
            self.generate_update()

    def incoming_request(self):
        """
        Checks reservation state prior to handling an incoming request. These
        checks are not applied to probes or closes.

        @throws Exception
        """
        assert self.slice_object is not None

        # Disallow any further requests on a closed delegation. Generate and update to reset the client.
        if self.is_closed():
            self.generate_update()
            self.error(err="server cannot satisfy request closing")

    def generate_update(self):
        self.logger.debug("Generating update")
        if self.callback is None:
            self.logger.warning("Cannot generate update: no callback.")
            return

        self.logger.debug("Generating update: update count={}".format(self.update_count))
        try:
            self.update_count += 1
            self.sequence_out += 1
            RPCManagerSingleton.get().update_delegation(delegation=self)
            self.must_send_update = False
        except Exception as e:
            # Note that this may result in a "stuck" reservation... not much we
            # can do if the receiver has failed or rejects our update. We will
            # regenerate on any user-initiated probe.
            self.logger.error("callback failed, exception={}".format(e))

    def map_and_update(self, *, delegated: bool):
        """
        Call the policy to fill a request, with associated state transitions.
        Catch exceptions and report all errors using callback mechanism.

        @param delegated
                   true if this is delegated (i.e., request is reclaim)
        @return boolean success
        """
        success = False
        granted = False

        if self.state == DelegationState.Nascent:
            if delegated:
                self.fail_notify(message="delegation is not yet delegated")
            else:
                self.logger.debug("Using policy {} to bind delegation".format(self.policy.__class__.__name__))
                try:
                    granted = False
                    # If the policy has processed this reservation, granted should
                    # be set true so that we can send the result back to the
                    # client. If the policy has not yet processed this reservation
                    # (binPending is true) then call the policy. The policy may
                    # choose to process the request immediately (true) or to defer
                    # it (false). In case of a deferred request, we will eventually
                    # come back to this method after the policy has done its job.
                    granted = self.policy.bind_delegation(delegation=self)

                except Exception as e:
                    self.logger.error("map_and_update bind_delegation failed for advertise: {e}")
                    self.fail_notify(message=str(e))
                    return success

                if granted:
                    self.logger.debug("Delegation {} has been granted".format(self.get_delegation_id()))
                    success = True
                    self.transition(prefix="delegated", state=DelegationState.Delegated)
        elif self.state == DelegationState.Delegated:
            if not delegated:
                self.fail_notify(message="delegation is already ticketed")
        else:
            self.logger.error("map_and_update: unexpected state")
            self.fail_notify(message="invalid operation for the current reservation state")

        return success

    def fail_notify(self, *, message: str):
        self.error_message = message
        self.generate_update()
        self.logger.error(message)

    def service_delegate(self):
        if self.dlg_graph_id is not None:
            # Update the graph
            self.transition(prefix="update absorbed", state=DelegationState.Delegated)
            self.generate_update()

    def prepare_probe(self):
        return

    def probe_pending(self):
        return

    def service_probe(self):
        if self.must_send_update:
            self.generate_update()

    def __str__(self):
        msg = "del: "
        if self.dlg_graph_id is not None:
            msg += "#{} ".format(self.dlg_graph_id)

        if self.slice_object is not None:
            msg += "slice: [{}] ".format(self.slice_object.get_name())
        elif self.slice_id is not None:
            msg += "slice_id: [{}] ".format(self.slice_id)

        msg += "state:[{}] ".format(self.get_state_name())

        if self.graph is not None:
            msg += "graph:[{}] ".format(self.graph)

        return msg

    def get_callback(self) -> ICallbackProxy:
        return self.callback

    def get_update_data(self) -> UpdateData:
        return self.update_data

    def set_sequence_in(self, value: int):
        self.sequence_in = value

    def get_sequence_in(self) -> int:
        return self.sequence_in

    def get_sequence_out(self) -> int:
        return self.sequence_out

    def update_delegation(self, *, incoming: IDelegation, update_data: UpdateData):
        self.error(err="Cannot update a authority delegation")

    def service_update_delegation(self):
        return

    def validate_incoming(self):
        if self.slice_object is None:
            self.error(err="No slice specified")

        if self.dlg_graph_id is None:
            self.error(err="No Graph specified")

        if self.graph is None:
            self.error(err="No Graph specified")

    def validate_outgoing(self):
        if self.slice_object is None:
            self.error(err="No slice specified")

        if self.dlg_graph_id is None:
            self.error(err="No Graph specified")

        if self.graph is None:
            self.error(err="No Graph specified")

    def set_owner(self, *, owner: AuthToken):
        self.owner = owner

    def load_graph(self, *, graph_str: str):
        self.graph = Neo4jResourcePoolFactory.get_graph_from_string(graph_str=graph_str)