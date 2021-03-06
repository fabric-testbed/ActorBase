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

from fabric_cf.actor.core.apis.i_client_reservation import IClientReservation
from fabric_cf.actor.core.apis.i_slice import ISlice

if TYPE_CHECKING:
    from fabric_cf.actor.core.apis.i_substrate import ISubstrate
    from fabric_cf.actor.core.common.resource_pool_descriptor import ResourcePoolDescriptor


class ResourcePoolException(Exception):
    """
    Resource Pool Exception
    """

class IResourcePoolFactory:
    @abstractmethod
    def set_substrate(self, *, substrate: ISubstrate):
        """
        Sets the substrate.
        @param substrate substrate
        @throws Exception in case of error
        """

    @abstractmethod
    def set_descriptor(self, *, descriptor: ResourcePoolDescriptor):
        """
        Sets the initial resource pools descriptor. The factory can modify the descriptor as needed.
        @param descriptor descriptor
        @throws Exception in case of error
        """

    @abstractmethod
    def get_descriptor(self) -> ResourcePoolDescriptor:
        """
        Returns the final pool descriptor.
        @return ResourcePoolDescriptor
        @throws Exception in case of error
        """

    @abstractmethod
    def create_source_reservation(self, *, slice_obj: ISlice) -> IClientReservation:
        """
        Returns the source reservation for this resource pool.
        @param slice_obj slice
        @return IClientReservation
        @throws Exception in case of error
        """
