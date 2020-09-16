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

from fabric.actor.core.apis.i_controller_policy import IControllerPolicy
from fabric.actor.core.kernel.controller_reservation_factory import ControllerReservationFactory
from fabric.actor.core.kernel.resource_set import ResourceSet
from fabric.actor.core.kernel.slice_factory import SliceFactory
from fabric.actor.core.time.term import Term
from fabric.actor.core.util.id import ID
from fabric.actor.core.util.resource_data import ResourceData
from fabric.actor.core.util.resource_type import ResourceType
from fabric.actor.test.core.policy.controller_simple_policy_test import ControllerSimplePolicyTest
from fabric.actor.test.core.policy.controller_ticket_review_policy_test_wrapper import \
    ControllerTicketReviewPolicyTestWrapper


class ControllerTicketReviewPolicyTest(ControllerSimplePolicyTest):
    def get_controller_policy(self) -> IControllerPolicy:
        return ControllerTicketReviewPolicyTestWrapper()

    def test_c_fail(self):
        controller = self.get_controller()
        clock = controller.get_actor_clock()
        Term.clock = clock

        resources = ResourceSet(units=1, rtype=ResourceType("1"), rdata=ResourceData())
        slice_obj = SliceFactory.create(ID(), "fail")
        controller.register_slice(slice_obj)

        start = 5
        end = 10

        term = Term(start=clock.cycle_start_date(start), end=clock.cycle_end_date(end))

        r1 = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        r1.set_renewable(False)
        controller.register(r1)
        controller.demand(r1.get_reservation_id())

        r2 = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        r2.set_renewable(False)
        controller.register(r2)
        controller.demand(r2.get_reservation_id())

        for i in range(1, end + 3):
            controller.external_tick(i)

            while controller.get_current_cycle() != i:
                time.sleep(0.001)

            if i >= start and (i < (end - 1)):
                self.assertTrue(r1.is_closed())
                self.assertTrue(r2.is_closed())

    def test_d_nascent(self):
        controller = self.get_controller()
        clock = controller.get_actor_clock()
        Term.clock = clock

        resources = ResourceSet(units=1, rtype=ResourceType("1"), rdata=ResourceData())
        slice_obj = SliceFactory.create(ID(), "nascent")
        controller.register_slice(slice_obj)

        start = 5
        end = 10

        term = Term(start=clock.cycle_start_date(start), end=clock.cycle_end_date(end))

        r1 = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        r1.set_renewable(False)
        controller.register(r1)
        controller.demand(r1.get_reservation_id())

        r2 = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        r2.set_renewable(False)
        controller.register(r2)

        r2demanded = False

        for i in range(1, end + 3):
            controller.external_tick(i)

            while controller.get_current_cycle() != i:
                time.sleep(0.001)

            if i == (start -3) and not r2demanded:
                self.assertTrue(r1.is_ticketed())
                self.assertTrue(r2.is_nascent())
                controller.demand(r2.get_reservation_id())
                r2demanded = True

            if i >= start and (i < end - 1):
                self.assertTrue(r1.is_active())
                self.assertTrue(r2.is_active())

            if i > end:
                self.assertTrue(r1.is_closed())
                self.assertTrue(r2.is_closed())

    def test_e_fail_and_nascent(self):
        controller = self.get_controller()
        clock = controller.get_actor_clock()
        Term.clock = clock

        resources = ResourceSet(units=1, rtype=ResourceType("1"), rdata=ResourceData())
        slice_obj = SliceFactory.create(ID(), "fail_nascent")
        controller.register_slice(slice_obj)

        start = 10
        end = 15

        term = Term(start=clock.cycle_start_date(start), end=clock.cycle_end_date(end))

        r1 = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        r1.set_renewable(False)
        controller.register(r1)
        controller.demand(r1.get_reservation_id())

        r2 = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        r2.set_renewable(False)
        controller.register(r2)
        r2demanded = False

        r3 = ControllerReservationFactory.create(ID(), resources=resources, term=term, slice_object=slice_obj)
        r3.set_renewable(False)
        controller.register(r3)
        controller.demand(r3.get_reservation_id())

        for i in range(1, end + 3):
            controller.external_tick(i)

            while controller.get_current_cycle() != i:
                time.sleep(0.001)

            if i > 2 and not r2demanded:
                self.assertTrue(r1.is_failed())
                self.assertTrue(r2.is_nascent())
                self.assertTrue(r3.is_ticketed())

                if i > 6:
                    controller.demand(r2.get_reservation_id())
                    r2demanded = True

            if (i >= start) and (i < (end - 1)):
                self.assertTrue(r1.is_closed())
                self.assertTrue(r2.is_closed())
                self.assertTrue(r3.is_closed())

            if i > end:
                self.assertTrue(r1.is_closed())
                self.assertTrue(r2.is_closed())
                self.assertTrue(r3.is_closed())
