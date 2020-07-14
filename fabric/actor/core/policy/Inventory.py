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

from fabric.actor.core.common.Constants import Constants
from fabric.actor.core.common.ResourcePoolAttributeDescriptor import ResourcePoolAttributeDescriptor, ResourcePoolAttributeType
from fabric.actor.core.common.ResourcePoolDescriptor import ResourcePoolDescriptor
from fabric.actor.core.policy.SimplerUnitsInventory import SimplerUnitsInventory
from fabric.actor.core.util.PropList import PropList
from fabric.actor.core.util.ReflectionUtils import ReflectionUtils
from fabric.actor.core.util import ResourceType

if TYPE_CHECKING:
    from fabric.actor.core.policy.InventoryForType import InventoryForType
    from fabric.actor.core.apis.IClientReservation import IClientReservation


class Inventory:
    def __init__(self):
        self.map = {}

    def contains_type(self, resource_type: ResourceType):
        if resource_type is None:
            raise Exception("Invalid argument")

        if resource_type in self.map:
            return True

        return False

    def get(self, resource_type: ResourceType) -> InventoryForType:
        if resource_type is None:
            raise Exception("Invalid argument")

        return self.map[resource_type]

    def remove(self, source: IClientReservation):
        """
        Removes the inventory derived from the specified source.
        @param source source reservation
        @return true if the inventory was update, false otherwise
        """
        rtype = source.get_type()

        if rtype in self.map:
            inv = self.map[rtype]
            if inv.source == source:
                self.map.pop(rtype)
                return True

        return False

    def get_new(self, reservation: IClientReservation):
        if reservation is None:
            raise Exception("Invalid argument")

        rtype = reservation.get_type()

        if rtype in self.map:
            raise Exception("There is already inventory for type: {}".format(rtype))

        properties = {}

        rset = reservation.get_resources()
        cset = rset.get_resources()
        ticket = cset.get_ticket()

        properties = ticket.get_properties()
        properties = PropList.merge_properties(rset.get_resource_properties(), properties)
        rpd = ResourcePoolDescriptor()
        rpd.reset(properties, None)

        desc_attr = rpd.get_attribute(Constants.ResourceClassInventoryForType)
        inv = None
        if desc_attr is not None:
            module_name, class_name = desc_attr.get_value().rsplit(".", 1)
            inv = ReflectionUtils.create_instance(module_name, class_name)
        else:
            inv = SimplerUnitsInventory()

        inv.set_type(rtype)
        inv.set_descriptor(rpd)
        inv.donate(reservation)

        self.map[rtype] = inv
        return inv

    def get_inventory(self) -> dict:
        return self.map

    def get_resource_pools(self) -> dict:
        result = {}
        count = 0
        for inv in self.map.values():
            rpd = inv.get_descriptor().clone()
            attr = ResourcePoolAttributeDescriptor()
            attr.set_type(ResourcePoolAttributeType.INTEGER)
            attr.set_key(Constants.ResourceAvailableUnits)
            attr.set_value(str(inv.get_free()))
            rpd.add_attribute(attr)
            result = rpd.save(result, Constants.PoolPrefix + str(count) + ".")
            count += 1

        result[Constants.PoolsCount] = len(self.map)
        return result