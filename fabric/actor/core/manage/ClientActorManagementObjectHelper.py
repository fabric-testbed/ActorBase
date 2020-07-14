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

import traceback
from datetime import datetime
from typing import TYPE_CHECKING

from fabric.actor.core.apis.IActorRunnable import IActorRunnable
from fabric.actor.core.apis.IControllerReservation import IControllerReservation
from fabric.actor.core.common.Constants import Constants
from fabric.actor.core.kernel.ControllerReservationFactory import ControllerReservationFactory
from fabric.actor.core.kernel.ReservationStates import ReservationStates, ReservationPendingStates
from fabric.actor.core.kernel.ResourceSet import ResourceSet
from fabric.actor.core.manage.Converter import Converter
from fabric.actor.core.manage.ManagementObject import ManagementObject
from fabric.actor.core.manage.ManagementUtils import ManagementUtils
from fabric.message_bus.messages.LeaseReservationMng import LeaseReservationMng
from fabric.actor.core.manage.messages.PoolInfoMng import PoolInfoMng
from fabric.actor.core.manage.messages.ResultPoolInfoMng import ResultPoolInfoMng
from fabric.actor.core.manage.messages.ResultProxyMng import ResultProxyMng
from fabric.actor.core.apis.IClientActorManagementObject import IClientActorManagementObject
from fabric.actor.core.manage.messages.ResultReservationMng import ResultReservationMng
from fabric.actor.core.manage.messages.ResultStringMng import ResultStringMng
from fabric.actor.core.manage.messages.ResultStringsMng import ResultStringsMng
from fabric.actor.core.time.Term import Term
from fabric.actor.core.util.ID import ID
from fabric.actor.core.util.PropList import PropList
from fabric.actor.core.util.ResourceData import ResourceData
from fabric.actor.core.util.ResourceType import ResourceType
from fabric.message_bus.messages.ResultAvro import ResultAvro
from fabric.actor.core.core.BrokerPolicy import BrokerPolicy

if TYPE_CHECKING:
    from fabric.actor.core.apis.IClientActor import IClientActor
    from fabric.actor.security.AuthToken import AuthToken
    from fabric.actor.core.manage.messages.ProxyMng import ProxyMng
    from fabric.message_bus.messages.TicketReservationMng import TicketReservationMng
    from fabric.actor.core.apis.IActor import IActor
    from fabric.message_bus.messages.ReservationMng import ReservationMng


class ClientActorManagementObjectHelper(IClientActorManagementObject):
    def __init__(self, client: IClientActor):
        self.client = client
        from fabric.actor.core.container.Globals import GlobalsSingleton
        self.logger = GlobalsSingleton.get().get_logger()

    def get_brokers(self, caller: AuthToken) -> ResultProxyMng:
        result = ResultProxyMng()
        result.status = ResultAvro()

        if caller is None:
            result.status.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            brokers = self.client.get_brokers()
            result.result = Converter.fill_proxies(brokers)
        except Exception as e:
            self.logger.error("get_brokers {}".format(e))
            result.status.set_code(Constants.ErrorInternalError)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def get_broker(self, broker_id: ID, caller: AuthToken) -> ResultProxyMng:
        result = ResultProxyMng()
        result.status = ResultAvro()

        if broker_id is None or caller is None:
            result.status.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            broker = self.client.get_broker(broker_id)
            if broker is not None:
                brokers = [broker]
                result.result = Converter.fill_proxies(brokers)
            else:
                result.status.set_code(Constants.ErrorNoSuchBroker)
        except Exception as e:
            traceback.print_exc()
            self.logger.error("get_broker {}".format(e))
            result.status.set_code(Constants.ErrorInternalError)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def add_broker(self, broker_proxy: ProxyMng, caller: AuthToken) -> ResultAvro:
        result = ResultAvro()

        if broker_proxy is None or caller is None:
            result.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            proxy = Converter.get_agent_proxy(broker_proxy)
            if proxy is None:
                result.set_code(Constants.ErrorInvalidArguments)
            else:
                self.client.add_broker(proxy)
        except Exception as e:
            self.logger.error("add_broker {}".format(e))
            result.set_code(Constants.ErrorInternalError)
            result = ManagementObject.set_exception_details(result, e)

        return result

    def get_pool_info(self, broker: ID, caller: AuthToken) -> ResultPoolInfoMng:
        result = ResultPoolInfoMng()
        result.status = ResultAvro()

        if broker is None or caller is None:
            result.status.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            b = self.client.get_broker(broker)
            if b is not None:
                request = BrokerPolicy.get_resource_pools_query()
                response = ManagementUtils.query(self.client, b, request)
                pools = BrokerPolicy.get_resource_pools(response)

                for rd in pools:
                    temp = {}
                    temp = rd.save(temp, None)
                    pi = PoolInfoMng()
                    pi.set_type(str(rd.get_resource_type()))
                    pi.set_name(rd.get_resource_type_label())
                    pi.set_properties(temp)

                    result.result.append(pi)
            else:
                result.status.set_code(Constants.ErrorNoSuchBroker)
        except Exception as e:
            self.logger.error("get_pool_info {}".format(e))
            result.status.set_code(Constants.ErrorInternalError)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def add_reservation_private(self, reservation: TicketReservationMng):
        result = ResultAvro()
        slice_id = ID(reservation.get_slice_id())
        rset = Converter.get_resource_set(reservation)
        term = Term(start=datetime.fromtimestamp(reservation.get_start() * 1000),
                    end=datetime.fromtimestamp(reservation.get_end() * 1000))

        broker = None

        if reservation.get_broker() is not None:
            broker = ID(reservation.get_broker())

        rc = ControllerReservationFactory.create(rid=ID(), resources=rset, term=term)
        rc.set_renewable(reservation.is_renewable())

        if rc.get_state() != ReservationStates.Nascent or rc.get_pending_state() != ReservationPendingStates.None_:
            result.set_code(Constants.ErrorInvalidReservation)
            result.set_message("Only reservations in Nascent.None can be added")
            return None, result

        slice_obj = self.client.get_slice(slice_id)

        if slice_obj is None:
            result.set_code(Constants.ErrorNoSuchSlice)
            return None, result

        rc.set_slice(slice_obj)

        proxy = None

        if broker is None:
            proxy = self.client.get_default_broker()
        else:
            proxy = self.client.get_broker(broker)

        if proxy is None:
            result.set_code(Constants.ErrorNoSuchBroker)
            return None, result

        rc.set_broker(proxy)
        self.client.register(rc)
        return rc.get_reservation_id(), result

    def add_reservation(self, reservation: TicketReservationMng, caller: AuthToken) -> ResultStringMng:
        result = ResultStringMng()
        result.status = ResultAvro()

        if reservation is None or reservation.get_slice_id() is None or caller is None:
            result.status.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            class Runner(IActorRunnable):
                def __init__(self, parent):
                    self.parent = parent

                def run(self):
                    return self.parent.add_reservation_private(reservation)

            rid, result.status = self.client.execute_on_actor_thread_and_wait(Runner(self))

            if rid is not None:
                result.result = str(rid)
        except Exception as e:
            self.logger.error("add_reservation {}".format(e))
            result.status.set_code(Constants.ErrorInternalError)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def add_reservations(self, reservations: list, caller: AuthToken) -> ResultStringsMng:
        result = ResultStringsMng()
        result.status = ResultAvro()

        if reservations is None or caller is None:
            result.status.set_code(Constants.ErrorInvalidArguments)
            return result

        for r in reservations:
            if r.get_slice_id() is None:
                result.status.set_code(Constants.ErrorInvalidArguments)
                return result

        try:
            class Runner(IActorRunnable):
                def __init__(self, parent):
                    self.parent = parent

                def run(self):
                    result = []
                    try:
                        for r in reservations:
                            rr, status = self.parent.add_reservation_private(r)
                            if rr is not None:
                                result.append(str(rr))
                            else:
                                raise Exception("Could not add reservation")
                    except Exception as e:
                        for r in reservations:
                            self.parent.client.unregister(r)
                        result.clear()

                    return result

            rids, result.status = self.client.execute_on_actor_thread_and_wait(Runner(self))

            if result.status.get_code() == 0:
                for r in rids:
                    result.result.append(r)
        except Exception as e:
            self.logger.error("add_reservations {}".format(e))
            result.status.set_code(Constants.ErrorInternalError)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def demand_reservation_rid(self, rid: ID, caller: AuthToken) -> ResultAvro:
        result = ResultAvro()

        if rid is None or caller is None:
            result.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            class Runner(IActorRunnable):
                def __init__(self, actor: IActor):
                    self.actor = actor

                def run(self):
                    self.actor.demand(rid)
                    return None

            self.client.execute_on_actor_thread_and_wait(Runner(self.client))
        except Exception as e:
            self.logger.error("demand_reservation_rid {}".format(e))
            result.set_code(Constants.ErrorInternalError)
            result = ManagementObject.set_exception_details(result, e)

        return result

    def demand_reservation(self, reservation: ReservationMng, caller: AuthToken) -> ResultAvro:
        result = ResultAvro()

        if reservation is None or caller is None:
            result.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            class Runner(IActorRunnable):
                def __init__(self, actor: IActor, logger):
                    self.actor = actor
                    self.logger = logger

                def run(self):
                    result = ResultAvro()
                    rid = ID(reservation.get_reservation_id())
                    r = self.actor.get_reservation(rid)
                    if r is None:
                        result.set_code(Constants.ErrorNoSuchReservation)
                        return result

                    ManagementUtils.update_reservation(r, reservation)
                    if isinstance(reservation, LeaseReservationMng):
                        predecessors = reservation.get_redeem_predecessors()
                        for pred in predecessors:
                            if pred.get_reservation_id() is None:
                                self.logger.warning("Redeem predecessor specified for rid={} but missing reservation id of predecessor".format(rid))
                                continue

                            predid = ID(pred.get_reservation_id())
                            pr = self.actor.get_reservation(predid)

                            if pr is None:
                                self.logger.warning("Redeem predecessor for rid={} with rid={} does not exist. Ignoring it!".format(rid, predid))
                                continue

                            if not isinstance(pr, IControllerReservation):
                                self.logger.warning("Redeem predecessor for rid={} is not an IControllerReservation: class={}".format(rid, type(pr)))
                                continue

                            ff = pred.get_filter()
                            if ff is not None:
                                self.logger.debug("Setting redeem predecessor on reservation # {} pred={} filter={}".format(r.get_reservation_id(), pr.get_reservation_id(), ff))
                                r.add_redeem_predecessor(pr, ff)
                            else:
                                self.logger.debug(
                                    "Setting redeem predecessor on reservation # {} pred={} filter=none".format(r.get_reservation_id(),
                                                                                                              pr.get_reservation_id()))
                                r.add_redeem_predecessor(pr)

                    try:
                        self.actor.get_plugin().get_database().update_reservation(r)
                    except Exception as e:
                        self.logger.error("Could not commit slice update {}".format(e))
                        result.set_code(Constants.ErrorDatabaseError)

                    self.actor.demand(rid)

                    return result

            result = self.client.execute_on_actor_thread_and_wait(Runner(self.client, self.logger))
        except Exception as e:
            self.logger.error("demand_reservation {}".format(e))
            result.set_code(Constants.ErrorInternalError)
            result = ManagementObject.set_exception_details(result, e)

        return result

    def claim_resources_slice(self, broker: ID, slice_id: ID, rid: ID, caller: AuthToken) -> ResultReservationMng:
        result = ResultReservationMng()
        result.status = ResultAvro()

        if caller is None or broker is None or slice_id is None or rid is None:
            result.status.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            rtype = ResourceType(str(ID()))
            rdata = ResourceData()
            rset = ResourceSet(units=0, rtype=rtype, rdata=rdata)

            my_broker = self.client.get_broker(broker)

            if my_broker is None:
                result.status.set_code(Constants.ErrorNoSuchBroker)
                return result

            slice_obj = self.client.get_slice(slice_id)
            if slice_obj is None:
                result.status.set_code(Constants.ErrorNoSuchSlice)
                return result

            if not slice_obj.is_inventory():
                result.status.set_code(Constants.ErrorInvalidSlice)
                return result

            class Runner(IActorRunnable):
                def __init__(self, actor: IActor):
                    self.actor = actor

                def run(self):
                    return self.actor.claim_client(reservation_id=rid, resources=rset, slice_obj=slice_obj, broker=my_broker)

            rc = self.client.execute_on_actor_thread_and_wait(Runner(self.client))

            if rc is not None:
                reservation = Converter.fill_reservation(rc, True)
                result.result.append(reservation)
            else:
                raise Exception("Internal Error")
        except Exception as e:
            self.logger.error("claim_resources_slice {}".format(e))
            result.status.set_code(Constants.ErrorInternalError)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def claim_resources(self, broker: ID, rid: ID, caller: AuthToken) -> ResultReservationMng:
        result = ResultReservationMng()
        result.status = ResultAvro()

        if caller is None or rid is None or broker is None:
            result.status.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            rtype = ResourceType(str(ID()))
            rdata = ResourceData()
            rset = ResourceSet(units=0, rtype=rtype, rdata=rdata)

            my_broker = self.client.get_broker(broker)

            if my_broker is None:
                result.status.set_code(Constants.ErrorNoSuchBroker)
                return result

            class Runner(IActorRunnable):
                def __init__(self, actor: IActor):
                    self.actor = actor

                def run(self):
                    return self.actor.claim_client(reservation_id=rid, resources=rset, broker=my_broker)

            rc = self.client.execute_on_actor_thread_and_wait(Runner(self.client))

            if rc is not None:
                reservation = Converter.fill_reservation(rc, True)
                result.result.append(reservation)
            else:
                raise Exception("Internal Error")
        except Exception as e:
            traceback.print_exc()
            self.logger.error("claim_resources {}".format(e))
            result.status.set_code(Constants.ErrorInternalError)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def extend_reservation(self, reservation: id, new_end_time: datetime, new_units: int,
                           new_resource_type: ResourceType, request_properties: dict,
                           config_properties: dict, caller: AuthToken) -> ResultAvro:
        result = ResultAvro()

        if reservation is None or caller is None or new_end_time is None:
            result.set_code(Constants.ErrorInvalidArguments)
            return result

        try:
            class Runner(IActorRunnable):
                def __init__(self, actor: IActor):
                    self.actor = actor

                def run(self):
                    result = ResultAvro()
                    r = self.actor.get_reservation(ID(reservation.get_reservation_id()))
                    if r is None:
                        result.set_code(Constants.ErrorNoSuchReservation)
                        return result

                    temp = PropList.merge_properties(r.get_resources().get_config_properties(), config_properties)
                    r.get_resources().set_config_properties(temp)

                    temp = PropList.merge_properties(r.get_resources().get_request_properties(), request_properties)
                    r.get_resources().set_request_properties(temp)

                    rset = ResourceSet()
                    if new_units == Constants.ExtendSameUnits:
                        rset.set_units(r.get_resources().get_units())
                    else:
                        rset.set_units(new_units)

                    if new_resource_type is None:
                        rset.set_type(r.get_resources().get_type())

                    rset.set_config_properties(config_properties)
                    rset.set_request_properties(request_properties)

                    tmp_start_time = r.get_term().get_start_time()
                    new_term = r.get_term().extend()

                    new_term.set_end_time(new_end_time)
                    new_term.set_new_start_time(tmp_start_time)
                    new_term.set_start_time(tmp_start_time)

                    self.actor.extend(r.get_reservation_id(), rset, new_term)

                    return result

            result = self.client.execute_on_actor_thread_and_wait(Runner(self.client))

        except Exception as e:
            self.logger.error("extend_reservation {}".format(e))
            result.set_code(Constants.ErrorInternalError)
            result = ManagementObject.set_exception_details(result, e)

        return result

    def modify_reservation(self, rid: ID, modify_properties: dict, caller: AuthToken) -> ResultAvro:
        result = ResultAvro()

        if rid is None or modify_properties is None:
            result.set_code(Constants.ErrorInvalidArguments)
            return result

        self.logger.debug("reservation: {} | modifyProperties= {}".format(rid, modify_properties))
        try:

            class Runner(IActorRunnable):
                def __init__(self, actor: IActor):
                    self.actor = actor

                def run(self):
                    result = ResultAvro()
                    r = self.actor.get_reservation(rid)
                    if r is None:
                        result.set_code(Constants.ErrorNoSuchReservation)
                        return result

                    self.actor.modify(rid, modify_properties)

                    return result
            result = self.client.execute_on_actor_thread_and_wait(Runner(self.client))
        except Exception as e:
            self.logger.error("modify_reservation {}".format(e))
            result.set_code(Constants.ErrorInternalError)
            result = ManagementObject.set_exception_details(result, e)

        return result