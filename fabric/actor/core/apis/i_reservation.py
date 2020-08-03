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

from fabric.actor.core.kernel.reservation_states import ReservationStates, ReservationPendingStates

if TYPE_CHECKING:
    from fabric.actor.core.apis.i_actor import IActor
    from fabric.actor.core.apis.i_slice import ISlice
    from fabric.actor.core.util.id import ID
    from fabric.actor.core.util.reservation_state import ReservationState
    from fabric.actor.core.util.resource_type import ResourceType

from fabric.actor.core.apis.i_reservation_resources import IReservationResources
from fabric.actor.core.apis.i_reservation_status import IReservationStatus


class IReservation(IReservationResources, IReservationStatus):
    """
    IReservation defines the the core API for a reservation. Most of the methods described in the interface allow the
    programmer to inspect the state of the reservation, access some of its core objects,
    and wait for the occurrence of a particular event.
    """

    # Unspecified reservation category.
    CategoryAll = 0
    # Client-side reservations.
    CategoryClient = 1
    # Broker-side reservations.
    CategoryBroker = 2
    # Site authority-side reservations.
    CategoryAuthority = 3

    # Serialization property name: reservation identifier.
    PropertyID = "rsv_resid"

    # Serialization property name: reservation category.
    PropertyCategory = "rsv_category"

    # Serialization property name: reservation slice name.
    PropertySlice = "rsv_slc_id"

    # Serialization property name: reservation state.
    PropertyState = "rsv_state"

    # Serialization property name: reservation pending state.
    PropertyPending = "rsv_pending"

    PropertyStateJoined = "rsv_joining"

    def clear_dirty(self):
        """
        Marks that the reservation has no uncommitted updates or state transitions.
        """
        raise NotImplementedError("Should have implemented this")

    def get_actor(self) -> IActor:
        """
        Returns the actor in control of the reservation.

        Returns:
            the actor in control of the reservation.
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_category(self) -> int:
        """
        Returns the reservation category.

        Returns:
            the reservation category.
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_pending_state(self) -> ReservationPendingStates:
        """
        Returns the current pending reservation state.

        Returns:
            current pending reservation state.
        """
        raise NotImplementedError("Should have implemented this")

    def get_pending_state_name(self) -> str:
        """
        Returns the current pending reservation state name

        Returns:
            current pending reservation state name
        """
        raise NotImplementedError("Should have implemented this")

    def get_reservation_id(self) -> ID:
        """
        Returns the reservation id.

        Returns:
            the reservation id.
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_reservation_state(self) -> ReservationState:
        """
        Returns the current composite reservation state.

        Returns:
            current composite reservation state.
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_slice(self) -> ISlice:
        """
        Returns the slice the reservation belongs to.

        Returns:
            slice the reservation belongs to.
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_slice_id(self) -> ID:
        """
        Returns the slice GUID.

        Returns:
            slice guid
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_slice_name(self) -> str:
        """
        Returns the slice name.

        Returns:
            slice name
        """
        raise NotImplementedError("Should have implemented this")

    def get_state(self) -> ReservationStates:
        """
        Returns the current reservation state.

        Returns:
            current reservation state.
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_state_name(self) -> str:
        """
        Returns the current reservation state name.

        Returns:
            current reservation state name.
        """
        raise NotImplementedError( "Should have implemented this" )

    def get_type(self) -> ResourceType:
        """
        Returns the resource type allocated to the reservation. If no resources have yet been allocated to the
        reservation, this method will return None.

        Returns:
            resource type allocated to the reservation. None if no resources have been allocated to the reservation.
        """
        raise NotImplementedError( "Should have implemented this" )

    def has_uncommitted_transition(self) -> bool:
        """
        Checks if the reservation has uncommitted state transitions.

        Returns:
            true if the reservation has an uncommitted transition
        """
        raise NotImplementedError( "Should have implemented this" )

    def is_dirty(self) -> bool:
        """
        Checks if the reservation has uncommitted updates.

        Returns:
            true if the reservation has an uncommitted updates
        """
        raise NotImplementedError( "Should have implemented this" )

    def is_pending_recover(self) -> bool:
        """
        Checks if a recovery operation is in progress for the reservation

        Returns:
            true if a recovery operation for the reservation is in progress
        """
        raise NotImplementedError( "Should have implemented this" )

    def set_dirty(self):
        """
        Marks the reservation as containing uncommitted updates.
        """
        raise NotImplementedError( "Should have implemented this" )

    def set_pending_recover(self, pending_recover:bool):
        """
        Indicates if a recovery operation for the reservation is going to be in progress.

        Args:
            pending_recover: true, a recovery operation is in progress, false - no recovery operation is in progress.
        """
        raise NotImplementedError( "Should have implemented this" )

    def set_slice(self, slice_object):
        """
        Sets the slice the reservation belongs to.

        Args:
            slice_object: slice the reservation belongs to
        """
        raise NotImplementedError( "Should have implemented this" )

    def transition(self, prefix: str, state: ReservationStates, pending: ReservationPendingStates):
        """
        Transitions this reservation into a new state.

        Args:
            prefix: prefix
            state: the new state
            pending: if reservation is pending
        """
        raise NotImplementedError("Should have implemented this" )

    def get_notices(self) -> str:
        raise NotImplementedError("Should have implemented this")