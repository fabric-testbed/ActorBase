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
import time
import unittest

from fabric.actor.core.apis.i_actor import IActor
from fabric.actor.core.apis.i_controller_policy import IControllerPolicy
from fabric.actor.core.common.constants import Constants
from fabric.actor.core.kernel.controller_reservation_factory import ControllerReservationFactory
from fabric.actor.core.kernel.reservation_states import ReservationStates
from fabric.actor.core.kernel.resource_set import ResourceSet
from fabric.actor.core.kernel.slice_factory import SliceFactory
from fabric.actor.core.time.term import Term
from fabric.actor.core.util.id import ID
from fabric.actor.core.util.resource_data import ResourceData
from fabric.actor.core.util.resource_type import ResourceType
from fabric.actor.test.base_test_case import BaseTestCase
from fabric.actor.test.core.policy.controller_simple_policy_test_wrapper import ControllerSimplePolicyTestWrapper
from fabric.actor.test.core.policy.controller_test_wrapper import ControllerTestWrapper


class ControllerSimplePolicyTest(BaseTestCase, unittest.TestCase):
    from fabric.actor.core.container.globals import Globals
    Globals.ConfigFile = Constants.TestControllerConfigurationFile

    from fabric.actor.core.container.globals import GlobalsSingleton
    GlobalsSingleton.get().start(True)
    while not GlobalsSingleton.get().start_completed:
        time.sleep(0.0001)

    def get_controller(self, name: str = BaseTestCase.ControllerName, guid: ID = BaseTestCase.ControllerGuid):
        db = self.get_container_database()
        db.reset_db()
        controller = super().get_controller()
        controller.set_recovered(True)
        Term.set_clock(controller.get_actor_clock())
        return controller

    def get_controller_instance(self) -> IActor:
        return ControllerTestWrapper()

    def get_controller_policy(self) -> IControllerPolicy:
        policy = ControllerSimplePolicyTestWrapper()
        return policy

    def test_a_create(self):
        controller = self.get_controller()
        for i in range(1, 101):
            controller.external_tick(i)

    def test_b_demand(self):
        controller = self.get_controller()
        clock = controller.get_actor_clock()
        Term.clock = clock
        resources = ResourceSet(units=1, rtype=ResourceType("1"), rdata=ResourceData())
        slice_obj = SliceFactory.create(ID(), "myslice")
        controller.register_slice(slice_obj)

        start = 5
        end = 10

        term = Term(start=clock.cycle_start_date(start), end=clock.cycle_end_date(end))

        reservation = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        reservation.set_renewable(False)
        controller.register(reservation)
        controller.demand(reservation.get_reservation_id())

        for i in range(1, end+3):
            controller.external_tick(i)
            while controller.get_current_cycle() != i:
                time.sleep(0.001)

            if (i >= start) and (i < (end-1)):
                self.assertTrue(reservation.get_state() == ReservationStates.Active)

            if i > end:
                self.assertTrue(reservation.get_state() == ReservationStates.Closed)
