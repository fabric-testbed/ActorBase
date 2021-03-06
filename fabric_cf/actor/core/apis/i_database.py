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

from abc import abstractmethod
from typing import TYPE_CHECKING

from fabric_cf.actor.core.apis.i_delegation import IDelegation

if TYPE_CHECKING:
    from fabric_cf.actor.core.apis.i_broker_proxy import IBrokerProxy
    from fabric_cf.actor.core.apis.i_reservation import IReservation
    from fabric_cf.actor.core.apis.i_slice import ISlice
    from fabric_cf.actor.core.util.id import ID
    from fabric_cf.actor.core.util.resource_type import ResourceType


class IDatabase:
    """
    IDatabase is the base database layer interface. It specifies methods for managing slices, reservations,
    broker proxies, and configuration mapping files.
    """

    @abstractmethod
    def actor_added(self):
        """
        Performs initialization actions as a result of the actor being
        added to the container.

        @throws Exception in case of error
        """

    @abstractmethod
    def add_broker(self, *, broker: IBrokerProxy):
        """
        Adds a new broker proxy record.

        @param broker broker proxy

        @throws Exception in case of error
        """

    @abstractmethod
    def add_reservation(self, *, reservation: IReservation):
        """
        Adds a new record to the database representing this reservation
        object.

        @param reservation reservation

        @throws Exception in case of error
        """

    @abstractmethod
    def add_slice(self, *, slice_object: ISlice):
        """
        Adds a new record to the database representing this slice
        object.

        @param slice_object Slice object

        @throws Exception in case of error
        """

    @abstractmethod
    def remove_broker(self, *, broker: IBrokerProxy):
        """
        Removes the specified broker proxy record.

        @param broker broker proxy

        @throws Exception in case of error
        """

    @abstractmethod
    def remove_reservation(self, *, rid: ID):
        """
        Removes the corresponding reservation object.

        @param rid reservation id

        @throws Exception in case of error
        """

    @abstractmethod
    def remove_slice(self, *, slice_id: ID):
        """
        Removes the corresponding database slice record.

        @param slice_id slice name

        @throws Exception in case of error
        """

    @abstractmethod
    def set_actor_name(self, *, name: str):
        """
        Sets the name of the actor this database belongs to.

        @param name actor name
        """

    @abstractmethod
    def update_broker(self, *, broker: IBrokerProxy):
        """
        Updates the specified broker proxy record.

        @param broker broker proxy

        @throws Exception in case of error
        """

    @abstractmethod
    def update_reservation(self, *, reservation: IReservation):
        """
        Updates the corresponding reservation object.

        @param reservation reservation

        @throws Exception in case of error
        """

    @abstractmethod
    def update_slice(self, *, slice_object: ISlice):
        """
        Updates the corresponding database slice record.

        @param slice_object slice object

        @throws Exception in case of error
        """

    @abstractmethod
    def get_reservations(self) -> list:
        """
        Retrieves the reservations.

        @return list of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_reservation(self, *, rid: ID) -> dict:
        """
        Retrieves the specified reservation record.

        @param rid Reservation identifier

        @return dict of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_reservations_by_slice_id(self, *, slice_id: ID) -> list:
        """
        Retrieves the specified reservations for a slice

        @param slice_id slice_id

        @return list of properties for reservations

        @throws Exception in case of error
        """

    @abstractmethod
    def get_reservations_by_slice_id_state(self, *, slice_id: ID, state: int) -> list:
        """
        Retrieves the specified reservations for a slice in a specific state

        @param slice_id slice_id
        @param state state

        @return list of properties for reservations

        @throws Exception in case of error
        """

    @abstractmethod
    def get_client_reservations(self) -> list:
        """
        Retrieves the client reservations

        @return list of properties for reservations

        @throws Exception in case of error
        """

    @abstractmethod
    def get_client_reservations_by_slice_id(self, *, slice_id: ID) -> list:
        """
        Retrieves the client reservations

        @param slice_id slice_id
        @return list of properties for reservations

        @throws Exception in case of error
        """

    @abstractmethod
    def get_slice(self, *, slice_id: ID) -> dict:
        """
        Retrieves the specified slice record.

        @param slice_id slice id

        @return dict of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_slice_by_resource_type(self, *, rtype: ResourceType) -> dict:
        """
        Retrieves the specified slice record.

        @param rtype resource type

        @return dict of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_slices(self) -> list:
        """
        Retrieves all slice records.

        @return a list containing one or more properties dicts representing
                serialized slices

        @throws Exception in case of error
        """

    @abstractmethod
    def get_inventory_slices(self) -> list:
        """
        Retrieves all inventory slice records.

        @return a list containing one or more properties dicts representing
                serialized slices

        @throws Exception in case of error
        """

    @abstractmethod
    def get_client_slices(self) -> list:
        """
        Retrieves all client slice records.

        @return a list containing one or more properties dicts representing
                serialized slices

        @throws Exception in case of error
        """

    @abstractmethod
    def initialize(self):
        """
        Initializes the object.

        @throws Exception if initialization fails
        """

    @abstractmethod
    def get_holdings(self) -> list:
        """
        Retrieves all reservations representing resources held by this
        actor Broker/Controller.

        @return list of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_holdings_by_slice_id(self, *, slice_id: ID) -> list:
        """
        Retrieves all reservations representing resources held by this
        actor Broker/Controller.
        @param slice_id sliceId

        @return vector of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_broker_reservations(self) -> list:
        """
        Retrieves all reservations for which this actor acts as a
        broker.

        @return list of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_authority_reservations(self) -> list:
        """
        Retrieves all reservations for which this actor acts as a site.

        @return list of properties

        @throws Exception in case of error
        """

    @abstractmethod
    def get_reservations_by_state(self, *, state: int) -> list:
        """
        Retrieves the reservations in a specific state

        @param state state

        @return list of properties for reservations

        @throws Exception in case of error
        """

    @abstractmethod
    def get_reservations_by_rids(self, *, rid: list):
        """
        Retrieves the specified reservation records.
        The order in the return vector is the same order as @rids
        @param rids rids
        @return list of properties
        @throws Exception in case of error
        """

    @abstractmethod
    def add_delegation(self, *, delegation: IDelegation):
        """
        Add delegation
        @params delegation: delegation
        """

    @abstractmethod
    def update_delegation(self, *, delegation: IDelegation):
        """
        Update delegation
        @params delegation: delegation
        """

    @abstractmethod
    def remove_delegation(self, *, dlg_graph_id: ID):
        """
        Remove delegation
        @params dlg_graph_id: dlg_graph_id
        """

    @abstractmethod
    def get_delegation(self, *, dlg_graph_id: ID) -> dict:
        """
        Get Delegation
        @params dlg_graph_id: dlg_graph_id
        """

    def get_delegations(self) -> list:
        """
        Get delegations
        """
