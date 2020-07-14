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

from fabric.actor.core.apis.IActor import IActor
from fabric.actor.core.apis.IClientPublic import IClientPublic

if TYPE_CHECKING:
    from fabric.actor.core.apis.IBrokerProxy import IBrokerProxy
    from fabric.actor.core.apis.IClientReservation import IClientReservation
    from fabric.actor.core.apis.ISlice import ISlice
    from fabric.actor.core.kernel.ResourceSet import ResourceSet
    from fabric.actor.core.util.ID import ID
    from fabric.actor.core.util.ReservationSet import ReservationSet


class IClientActor(IActor, IClientPublic):
    """
    IClientActor defines the common functionality for actors acting
    as clients of other actors (controllers and brokers). Every client actor
    is connected to one or more server actors. Each server actor is represented
    as a proxy object. Client actors maintain a registry of proxies to server
    actors that they are connected to. Proxies to actors acting in the broker
    role are explicitly managed. Proxies for actors acting in the site authority
    role are automatically managed as they are embedded in tickets sent from brokers.
    """
    def add_broker(self, broker: IBrokerProxy):
        """
        Registers a broker. If this is the first broker to be registered, it is
        set as the default broker.
        
        @params broker broker to register
        """
        raise NotImplementedError("Should have implemented this")

    def claim_client(self, reservation_id: ID = None, resources: ResourceSet = None, slice_object: ISlice = None, broker: IBrokerProxy = None) -> IClientReservation:
        """
        Claims already exported resources from the given broker. The reservation
        will be stored in the default slice.
        
        @params reservation_id reservation identifier of the exported reservation
        @params resources resource set describing the resources to claim
        @params slice_object slice
        @params broker broker proxy
        
        @returns reservation
        @raises Exception in case of failure
        """
        raise NotImplementedError("Should have implemented this")

    def demand(self, reservation: ID):
        raise NotImplementedError("Should have implemented this")

    def extend_ticket_client(self, reservation: IClientReservation):
        """
        Issues a ticket extend request for the given reservation. Note: the
        reservation must have already been registered with the actor.
        
        @param reservation reservation to extend the ticket for
        @param rset set of reservations to extend tickets for
        
        @throws Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def extend_tickets_client(self, rset: ReservationSet):
        """
        Issues a ticket extend request for the given reservation. Note: the
        reservation must have already been registered with the actor.

        @param reservation reservation to extend the ticket for
        @param rset set of reservations to extend tickets for

        @throws Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def get_broker(self, guid: ID) -> IBrokerProxy:
        """
        Gets the broker proxy with the given guid
        
        @param guid broker guid
        
        @return requested broker
        """
        raise NotImplementedError("Should have implemented this")

    def get_brokers(self) -> list:
        """
        Returns all brokers registered with the actor.
        
        @return an array of brokers
        """
        raise NotImplementedError("Should have implemented this")

    def get_default_broker(self) -> IBrokerProxy:
        """
        Returns the default broker.
        
        @return the default broker
        """
        raise NotImplementedError("Should have implemented this")

    def ticket_client(self, reservation: IClientReservation):
        """
        Issues a ticket request for the given reservation. Note: the reservation
        must have already been registered with the actor.
        
        All exceptions are caught and logged but no exception is propagated. No information will
        be delivered to indicate that some failure has taken place, e.g., failure
        to communicate with a broker. Inspect the state of individual
        reservations to determine whether/what failures have taken place.
        
        @param reservation reservation to obtain a ticket for

        @throws Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def tickets_client(self, rset: ReservationSet):
        """
        Issues a ticket request for the given reservation. Note: the reservation
        must have already been registered with the actor.

        All exceptions are caught and logged but no exception is propagated. No information will
        be delivered to indicate that some failure has taken place, e.g., failure
        to communicate with a broker. Inspect the state of individual
        reservations to determine whether/what failures have taken place.

        @param rset set of reservations to obtain tickets for

        @throws Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def modify(self, reservation_id: ID, modify_properties: dict):
        """
        Issue modify request for given reservation. Note: the reservation
        must have already been registered with the actor.
       
        @param reservation_id reservationID for the reservation to modify
        @param modify_properties property list for modify
        @throws Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")