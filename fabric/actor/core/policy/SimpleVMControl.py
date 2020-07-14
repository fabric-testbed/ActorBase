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
from fabric.actor.core.common.ResourcePoolDescriptor import ResourcePoolDescriptor
from fabric.actor.core.core.Unit import Unit, UnitState
from fabric.actor.core.core.UnitSet import UnitSet
from fabric.actor.core.policy.ResourceControl import ResourceControl
from fabric.actor.core.policy.VMControl import VMControl
from fabric.actor.core.util.ID import ID
from fabric.actor.core.util.IPv4Set import IPv4Set

if TYPE_CHECKING:
    from fabric.actor.core.util.ResourceType import ResourceType
    from fabric.actor.core.apis.IClientReservation import IClientReservation
    from fabric.actor.core.apis.IAuthorityReservation import IAuthorityReservation
    from fabric.actor.core.kernel.ResourceSet import ResourceSet
    from fabric.actor.core.apis.IReservation import IReservation


class PoolData:
    def __init__(self, rtype: ResourceType, properties: dict):
        self.total = 0
        self.free_ = 0
        self.rtype = rtype
        self.pd = ResourcePoolDescriptor()
        self.pd.reset(properties, None)

    def add_units(self, count: int):
        self.total += count
        self.free_ += count

    def allocate(self, count: int):
        if self.free_ < count:
            raise Exception("insufficient units (allocate): needed= {} available: {}".format(count, self.free_))

        self.free_ -= count

    def free(self, count: int):
        if self.free_ + count > self.total:
            raise Exception("too many units to free")

        self.free_ += count

    def reserve(self, count: int):
        if self.free_ < count:
            raise Exception("insufficient units (allocate): needed= {} available: {}".format(count, self.free_))

        self.free_ -= count

    def get_free(self) -> int:
        return self.free_

    def get_total(self) -> int:
        return self.total

    def get_allocated(self) -> int:
        return self.total - self.free_

    def get_descriptor(self) -> ResourcePoolDescriptor:
        return self.pd

    def get_type(self):
        return self.rtype


class SimpleVMControl(ResourceControl):
    def __init__(self):
        super().__init__()
        self.inventory = {}
        self.ipset = IPv4Set()
        self.subnet = None
        self.gateway = None
        self.data_subnet = None
        self.use_ip_set = False

    def __getstate__(self):
        state = self.__dict__.copy()

        del state['authority']
        del state['logger']
        del state['initialized']

        del state['inventory']
        del state['ipset']
        del state['subnet']
        del state['gateway']
        del state['data_subnet']
        del state['use_ip_set']

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.authority = None
        self.logger = None
        self.initialized = False

        self.inventory = {}
        self.ipset = IPv4Set()
        self.subnet = None
        self.gateway = None
        self.data_subnet = None
        self.use_ip_set = False

    def donate_reservation(self, reservation: IClientReservation):
        rset = reservation.get_resources()
        rtype = rset.get_type()
        resource = rset.get_resource_properties()
        local = rset.get_local_properties()

        pool = self.inventory.get(rtype)
        if pool is None:
            pool = PoolData(rtype, resource)
            pool.add_units(rset.get_units())
            if VMControl.PropertyIPSubnet in local:
                self.subnet = local[VMControl.PropertyIPSubnet]
            if VMControl.PropertyIPGateway in local:
                self.gateway = local[VMControl.PropertyIPGateway]
            if VMControl.PropertyDataSubnet in local:
                self.data_subnet = local[VMControl.PropertyDataSubnet]
            if VMControl.PropertyIPList in local:
                temp = local[VMControl.PropertyIPList]
                self.ipset.add(temp)
                self.use_ip_set = True
            self.inventory[rtype] = pool
        else:
            pool.add_units(rset.get_units())

    def assign(self, reservation: IAuthorityReservation) -> ResourceSet:
        reservation.set_send_with_deficit(True)
        if len(self.inventory) == 0:
            raise Exception("no inventory")
        requested = reservation.get_requested_resources()
        request_properties = requested.get_resource_properties()
        rtype = requested.get_type()
        current = reservation.get_resources()

        ticket = requested.get_resources()
        term = reservation.get_requested_term()
        start = self.authority.get_actor_clock().cycle(when=term.get_new_start_time())
        end = self.authority.get_actor_clock().cycle(when=term.get_end_time())

        gained = None
        lost = None
        if current is None:
            pool = self.inventory.get(rtype)
            if pool is None:
                raise Exception("no resources of the specified pool")

            needed = ticket.get_units()
            gained = self.get_vms(pool, needed)
            if gained is None or gained.get_units() == 0:
                self.logger.warning("Could not allocate any units for r: {}".format(reservation.get_reservation_id()))
                return None
        else:
            rtype = current.get_type()
            pool = self.inventory.get(rtype)
            current_units = current.get_units()
            difference = ticket.get_units() - current_units
            if difference > 0:
                gained = self.get_vms(pool, difference)
            elif difference < 0:
                uset = current.get_resources()
                victims = request_properties[Constants.ConfigVictims]
                to_take = uset.select_extract(-difference, victims)
                lost = UnitSet(self.authority.get_plugin(), to_take)
        return ResourceSet(gained=gained, lost=lost, rtype=rtype)

    def get_vms(self, pool: PoolData, needed: int) -> UnitSet:
        uset = UnitSet(self.authority.get_plugin())
        available = min(needed, pool.get_free())

        if self.use_ip_set:
            available = min(available, self.ipset.get_free_count())

            pool.allocate(available)

            self.logger.debug("Allocated {} units".format(available))

            for i in range(available):
                vm = Unit(id=ID())
                vm.set_resource_type(pool.get_type())

                if self.use_ip_set:
                    vm.set_property(Constants.UnitManagementIP, self.ipset.allocate())

                if self.subnet is not None:
                    vm.set_property(Constants.UnitManageSubnet, self.subnet)

                if self.data_subnet is not None:
                    vm.set_property(Constants.UnitDataSubnet, self.data_subnet)

                if self.gateway is not None:
                    vm.set_property(Constants.UnitManageGateway, self.gateway)

                for att in pool.get_descriptor().get_attributes():
                    if att.get_value() is not None:
                        key = att.get_key()
                        key = key.replace("^resource\\.", "unit.")
                        vm.set_property(key, att.get_value())

                uset.add_unit(vm)
        return uset

    def free(self, uset: dict):
        if uset is not None:
            for u in uset.values():
                try:
                    self.logger.debug("Freeing 1 unit")
                    rtype =  u.get_resource_type()
                    pool = self.inventory.get(rtype)
                    pool.free(1)
                    if self.use_ip_set:
                        self.ipset.free(u.get_property(Constants.UnitManagementIP))
                except Exception as e:
                    self.logger.error("Failed to release vm {}".format(e))

    def revisit(self, reservation: IReservation):
        unit_set = reservation.get_resources().get_resources()
        for u in unit_set.get_set().values():
            try:
                if u.get_state() == UnitState.DEFAULT or \
                        u.get_state() == UnitState.FAILED or \
                        u.get_state() == UnitState.CLOSING or \
                        u.get_state() == UnitState.PRIMING or \
                        u.get_state() == UnitState.ACTIVE or \
                        u.get_state() == UnitState.MODIFYING:
                    rtype = u.get_resource_type()
                    pool = self.inventory.get(rtype)
                    pool.reserve(1)
                    mgmt_ip = u.get_property(Constants.UnitManagementIP)
                    if mgmt_ip is not None:
                        self.ipset.reserve(mgmt_ip)
            except Exception as e:
                self.fail(u, "revisit with simplemcontrol", e)