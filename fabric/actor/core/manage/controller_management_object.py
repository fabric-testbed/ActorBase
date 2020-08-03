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

from datetime import datetime
from typing import TYPE_CHECKING

from fabric.actor.core.common.constants import Constants, ErrorCodes
from fabric.actor.core.manage.actor_management_object import ActorManagementObject
from fabric.actor.core.manage.client_actor_management_object_helper import ClientActorManagementObjectHelper
from fabric.actor.core.manage.converter import Converter
from fabric.actor.core.manage.management_object import ManagementObject
from fabric.actor.core.manage.proxy_protocol_descriptor import ProxyProtocolDescriptor
from fabric.actor.core.apis.i_client_actor_management_object import IClientActorManagementObject
from fabric.actor.core.manage.messages.result_unit_mng import ResultUnitMng
from fabric.message_bus.messages.result_avro import ResultAvro

if TYPE_CHECKING:
    from fabric.actor.core.apis.i_controller import IController
    from fabric.actor.core.apis.i_actor import IActor
    from fabric.actor.core.manage.messages.result_proxy_mng import ResultProxyMng
    from fabric.actor.security.auth_token import AuthToken
    from fabric.actor.core.util.id import ID
    from fabric.actor.core.manage.messages.proxy_mng import ProxyMng
    from fabric.actor.core.manage.messages.result_pool_info_mng import ResultPoolInfoMng
    from fabric.message_bus.messages.result_string_avro import ResultStringAvro
    from fabric.message_bus.messages.ticket_reservation_avro import TicketReservationAvro
    from fabric.message_bus.messages.result_strings_avro import ResultStringsAvro
    from fabric.message_bus.messages.reservation_mng import ReservationMng
    from fabric.message_bus.messages.result_reservation_avro import ResultReservationAvro
    from fabric.actor.core.util.resource_type import ResourceType
    from fabric.actor.core.apis.i_substrate_database import ISubstrateDatabase


class ControllerManagementObject(ActorManagementObject, IClientActorManagementObject):
    def __init__(self, actor: IController = None):
        super().__init__(actor)
        self.client_helper = ClientActorManagementObjectHelper(actor)

    def register_protocols(self):
        from fabric.actor.core.manage.local.local_controller import LocalController
        local = ProxyProtocolDescriptor(Constants.ProtocolLocal, LocalController.__name__, LocalController.__module__)

        from fabric.actor.core.manage.kafka.kafka_controller import KafkaController
        kakfa = ProxyProtocolDescriptor(Constants.ProtocolKafka, KafkaController.__name__, KafkaController.__module__)

        self.proxies = []
        self.proxies.append(local)
        self.proxies.append(kakfa)

    def save(self) -> dict:
        properties = super().save()
        properties[Constants.PropertyClassName] = ControllerManagementObject.__name__,
        properties[Constants.PropertyModuleName] = ControllerManagementObject.__name__

        return properties

    def set_actor(self, actor: IActor):
        if self.actor is None:
            super().set_actor(actor)
            self.client_helper = ClientActorManagementObjectHelper(actor)

    def get_brokers(self, caller: AuthToken) -> ResultProxyMng:
        return self.client_helper.get_brokers(caller)

    def get_broker(self, broker_id: ID, caller: AuthToken) -> ResultProxyMng:
        return self.client_helper.get_broker(broker_id, caller)

    def add_broker(self, broker_proxy: ProxyMng, caller: AuthToken) -> ResultAvro:
        return self.client_helper.add_broker(broker_proxy, caller)

    def get_pool_info(self, broker: ID, caller: AuthToken) -> ResultPoolInfoMng:
        return self.client_helper.get_pool_info(broker, caller)

    def add_reservation(self, reservation: TicketReservationAvro, caller: AuthToken) -> ResultStringAvro:
        return self.client_helper.add_reservation(reservation, caller)

    def add_reservations(self, reservations: list, caller: AuthToken) -> ResultStringsAvro:
        return self.client_helper.add_reservations(reservations, caller)

    def demand_reservation_rid(self, rid: ID, caller: AuthToken) -> ResultAvro:
        return self.client_helper.demand_reservation_rid(rid, caller)

    def demand_reservation(self, reservation: ReservationMng, caller: AuthToken) -> ResultAvro:
        return self.client_helper.demand_reservation(reservation, caller)

    def claim_resources(self, broker: ID, rid: ID, caller: AuthToken) -> ResultReservationAvro:
        return self.client_helper.claim_resources(broker, rid, caller)

    def claim_resources_slice(self, broker: ID, slice_id: ID, rid: ID, caller: AuthToken) -> ResultReservationAvro:
        return self.client_helper.claim_resources_slice(broker, slice_id, rid, caller)

    def extend_reservation(self, reservation: id, new_end_time: datetime, new_units: int,
                           new_resource_type: ResourceType, request_properties: dict,
                           config_properties: dict, caller: AuthToken) -> ResultAvro:
        return self.client_helper.extend_reservation(reservation, new_end_time, new_units, new_resource_type,
                                                     request_properties, config_properties, caller)

    def modify_reservation(self, rid: ID, modify_properties: dict, caller: AuthToken) -> ResultAvro:
        return self.client_helper.modify_reservation(rid, modify_properties, caller)

    def get_reservation_units(self, caller: AuthToken, rid: ID) -> ResultUnitMng:
        result = ResultUnitMng()
        result.status = ResultAvro()

        if caller is None:
            result.status.set_code(ErrorCodes.ErrorInvalidArguments.value)
            result.status.set_message(ErrorCodes.ErrorInvalidArguments.name)
            return result
        try:
            units_list = None
            try:
                units_list = self.db.get_units(rid)
            except Exception as e:
                self.logger.error("get_reservation_units:db access {}".format(e))
                result.status.set_code(ErrorCodes.ErrorDatabaseError.value)
                result.status.set_message(ErrorCodes.ErrorDatabaseError.name)
                result.status = ManagementObject.set_exception_details(result.status, e)
                return result

            if units_list is not None:
                result.result = Converter.fill_units(units_list)
        except Exception as e:
            self.logger.error("get_reservation_units: {}".format(e))
            result.status.set_code(ErrorCodes.ErrorInternalError.value)
            result.status.set_message(ErrorCodes.ErrorInternalError.name)
            result.status = ManagementObject.set_exception_details(result.status, e)

        return result

    def get_substrate_database(self) -> ISubstrateDatabase:
        return self.actor.get_plugin().get_database()