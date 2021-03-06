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


if TYPE_CHECKING:
    from fim.graph.abc_property_graph import ABCPropertyGraph

    from fabric_cf.actor.core.kernel.slice import SliceTypes
    from fabric_cf.actor.security.auth_token import AuthToken
    from fabric_cf.actor.core.util.resource_type import ResourceType
    from fabric_cf.actor.core.util.id import ID
    from fabric_cf.actor.core.util.resource_data import ResourceData


class ISlice:
    """
    ISlice describes the programming interface to a slice object. Each slice has a name (not necessarily unique)
    and a globally unique identifier. Slices are used to organize groups of reservations. Each reservation belongs
    to exactly one slice. Slices information is passed to upstream actors as part of ticket and lease requests.
    There are several slice types:
        inventory slices: are used to organized reservations that represent an inventory.
                          For example, allocated resources, or resources to be used to satisfy client requests
        client slices: are used on server actors to group reservations representing client requests
                       (allocated/assigned resources).
        broker client slices: are client slices that represent the requests from a broker that acts as a
                              client of the containing actor

    Each slice contains a number of properties lists, which can be used to store properties applicable to all
    reservations associated with the slice. Properties defined in the slice are automatically inherited by reservations.
    Each reservation can also override a property inherited by the slice, but defining it in its appropriate
    properties list.
    """

    @abstractmethod
    def get_config_properties(self) -> dict:
        """
        Returns the slice configuration properties list

        Returns:
            configuration properties list
        """

    @abstractmethod
    def get_local_properties(self) -> dict:
        """
        Returns the slice local properties list

        Returns:
            local properties list
        """

    @abstractmethod
    def get_description(self) -> str:
        """
        Returns the slice description

        Returns:
            slice description
        """

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the slice name

        Returns:
            slice name
        """

    @abstractmethod
    def get_owner(self) -> AuthToken:
        """
        Returns the slice owner

        Returns:
            slice owner
        """

    @abstractmethod
    def get_properties(self) -> dict:
        """
        Returns the slice properties

        Returns:
            slice properties
        """

    @abstractmethod
    def get_request_properties(self) -> dict:
        """
        Returns the slice request properties list

        Returns:
            slice request properties list
        """

    @abstractmethod
    def get_resource_properties(self) -> dict:
        """
        Returns the slice resource properties list

        Returns:
            slice resource properties list
        """

    @abstractmethod
    def get_resource_type(self) -> ResourceType:
        """
        Returns the resource type of the slice (if any).

        Returns:
            slice resource type
        """

    @abstractmethod
    def get_slice_id(self) -> ID:
        """
        Returns the slice id.

        Returns:
            slice id
        """

    @abstractmethod
    def is_broker_client(self) -> bool:
        """
        Checks if the slice is a broker client slice (a client slice within an authority that represents a broker).

        Returns:
            true if the slice is a broker client slice
        """

    @abstractmethod
    def is_client(self) -> bool:
        """
        Checks if the slice is a client slice.

        Returns:
            true if the slice is a client slice
        """

    @abstractmethod
    def is_inventory(self) -> bool:
        """
        Checks if the slice is a inventory slice.

        Returns:
            true if the slice is a inventory slice
        """

    @abstractmethod
    def set_broker_client(self):
        """
        Marks the slice as a broker client slice (a client slice within an authority that represents a broker).
        """

    @abstractmethod
    def set_client(self):
        """
        Marks the slice as a client slice.
        """

    @abstractmethod
    def set_inventory(self, *, value: bool):
        """
        Sets the inventory flag.

        Args:
            value: inventory status: true, inventory slice, false, client slice
        """

    @abstractmethod
    def set_description(self, *, description: str):
        """
        Sets the slice description.

        Args:
            description: description
        """

    @abstractmethod
    def set_name(self, *, name: str):
        """
        Sets the slice name.

        Args:
            name: name
        """

    @abstractmethod
    def set_owner(self, *, owner: AuthToken):
        """
        Sets the slice owner.

        Args:
            owner: owner
        """

    @abstractmethod
    def set_resource_type(self, *, resource_type: ResourceType):
        """
        Sets the resource type.

        Args:
            resource_type: resource type
        """

    @abstractmethod
    def clone_request(self):
        """
        Makes a minimal clone of the slice object sufficient for
        cross-actor calls.

        @return a slice object to use when making cross-actor calls.
        """

    @abstractmethod
    def set_local_properties(self, *, value: dict):
        """
        Set local properties
        @param value: value
        """

    @abstractmethod
    def set_config_properties(self, *, value: dict):
        """
        Set config properties
        @param value: value
        """

    @abstractmethod
    def set_request_properties(self, *, value: dict):
        """
        Set request properties
        @param value: value
        """

    @abstractmethod
    def set_resource_properties(self, *, value: dict):
        """
        Set resource properties
        @param value: value
        """
    @abstractmethod
    def get_slice_type(self) -> SliceTypes:
        """
        Return slice type
        """

    @abstractmethod
    def set_graph(self, *, graph: ABCPropertyGraph):
        """
        Sets the resource model graph.

        @param graph graph
        """

    @abstractmethod
    def get_graph(self) -> ABCPropertyGraph:
        """
        Gets the resource model graph.
        """

    @abstractmethod
    def set_graph_id(self, graph_id: ID):
        """
        Set graph id
        @param graph_id:  graph_id
        """

    @abstractmethod
    def get_graph_id(self) -> ID:
        """
        Returns the graph id

        @return graph id
        """

    @abstractmethod
    def set_properties(self, *, rsrcdata: ResourceData):
        """
        Sets the slice properties.
        @param properties slice properties
        """
