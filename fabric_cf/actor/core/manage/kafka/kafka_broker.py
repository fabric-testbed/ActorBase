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
from typing import List

import traceback

from fabric_mb.message_bus.messages.add_reservation_avro import AddReservationAvro
from fabric_mb.message_bus.messages.add_reservations_avro import AddReservationsAvro
from fabric_mb.message_bus.messages.claim_resources_avro import ClaimResourcesAvro
from fabric_mb.message_bus.messages.delegation_avro import DelegationAvro
from fabric_mb.message_bus.messages.demand_reservation_avro import DemandReservationAvro
from fabric_mb.message_bus.messages.extend_reservation_avro import ExtendReservationAvro
from fabric_mb.message_bus.messages.get_actors_request_avro import GetActorsRequestAvro
from fabric_mb.message_bus.messages.get_pool_info_request_avro import GetPoolInfoRequestAvro
from fabric_mb.message_bus.messages.pool_info_avro import PoolInfoAvro
from fabric_mb.message_bus.messages.proxy_avro import ProxyAvro
from fabric_mb.message_bus.messages.reclaim_resources_avro import ReclaimResourcesAvro
from fabric_mb.message_bus.messages.reservation_mng import ReservationMng
from fabric_mb.message_bus.messages.result_avro import ResultAvro
from fabric_mb.message_bus.messages.ticket_reservation_avro import TicketReservationAvro

from fabric_cf.actor.core.apis.i_actor import ActorType
from fabric_cf.actor.core.common.constants import Constants, ErrorCodes
from fabric_cf.actor.core.apis.i_mgmt_broker import IMgmtBroker
from fabric_cf.actor.core.common.exceptions import ManageException
from fabric_cf.actor.core.manage.kafka.kafka_server_actor import KafkaServerActor
from fabric_cf.actor.core.util.id import ID
from fabric_cf.actor.core.util.resource_type import ResourceType


class KafkaBroker(KafkaServerActor, IMgmtBroker):
    def add_reservation(self, *, reservation: TicketReservationAvro) -> ID:
        self.clear_last()
        status = ResultAvro()
        rret_val = None

        try:
            request = AddReservationAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.reservation_obj = reservation

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
                    if status.code == 0:
                        rret_val = message_wrapper.response.result_str
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name

        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return rret_val

    def add_reservations(self, *, reservations: list) -> List[TicketReservationAvro]:
        self.clear_last()
        status = ResultAvro()
        rret_val = None

        try:
            request = AddReservationsAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.reservation_list = reservations

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
                    if status.code == 0:
                        rret_val = message_wrapper.response.result
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name

        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return rret_val

    def demand_reservation(self, *, reservation: ReservationMng) -> bool:
        self.clear_last()
        status = ResultAvro()

        try:
            request = DemandReservationAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.reservation_obj = reservation

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name

        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return status.code == 0

    def demand_reservation_rid(self, *, rid: ID) -> bool:
        self.clear_last()
        status = ResultAvro()

        try:
            request = DemandReservationAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.reservation_id = str(rid)

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name

        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return status.code == 0

    def get_brokers(self, *, broker: ID = None, id_token: str = None) -> List[ProxyAvro]:
        self.clear_last()
        status = ResultAvro()
        rret_val = None

        try:
            request = GetActorsRequestAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.type = ActorType.Broker.name
            request.id_token = id_token
            request.broker_id = broker

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
                    if status.code == 0:
                        rret_val = message_wrapper.response.proxies
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name

        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return rret_val

    def get_pool_info(self, *, broker: ID, id_token: str) -> List[PoolInfoAvro]:
        self.clear_last()
        status = ResultAvro()
        rret_val = None

        try:
            request = GetPoolInfoRequestAvro()
            request.id_token = id_token
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.broker_id = str(broker)

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
                    if status.code == 0:
                        rret_val = message_wrapper.response.pools
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name

        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return rret_val

    def extend_reservation_end_time(self, *, reservation: ID, new_end_time: datetime) -> bool:
        return self.extend_reservation(reservation=reservation, new_end_time=new_end_time,
                                       new_units=Constants.extend_same_units)

    def extend_reservation_end_time_request(self, *, reservation: ID, new_end_time: datetime,
                                            request_properties: dict) -> bool:
        return self.extend_reservation(reservation=reservation, new_end_time=new_end_time,
                                       new_units=Constants.extend_same_units,
                                       request_properties=request_properties)

    def extend_reservation_end_time_request_config(self, *, reservation: ID, new_end_time: datetime,
                                                   request_properties: dict, config_properties: dict) -> bool:
        return self.extend_reservation(reservation=reservation, new_end_time=new_end_time,
                                       new_units=Constants.extend_same_units,
                                       request_properties=request_properties,
                                       config_properties=config_properties)

    def extend_reservation(self, *, reservation: ID, new_end_time: datetime, new_units: int,
                           new_resource_type: ResourceType = None, request_properties: dict = None,
                           config_properties: dict = None) -> bool:
        self.clear_last()
        status = ResultAvro()

        try:
            request = ExtendReservationAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.rid = str(reservation)
            if new_units is not None:
                request.new_units = new_units
            request.new_resource_type = new_resource_type
            request.request_properties = request_properties
            request.config_properties = config_properties

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name

        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return status.code == 0

    def claim_delegations(self, *, broker: ID, did: ID, id_token: str = None) -> DelegationAvro:
        self.clear_last()
        status = ResultAvro()
        rret_val = None

        try:
            request = ClaimResourcesAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.broker_id = str(broker)
            request.delegation_id = did
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.id_token = id_token

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
                    if status.code == 0 and message_wrapper.response.delegations is not None and len(
                            message_wrapper.response.delegations) > 0:
                        rret_val = next(iter(message_wrapper.response.delegations))
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name
        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return rret_val

    def reclaim_delegations(self, *, broker: ID, did: ID, id_token: str = None) -> DelegationAvro:
        self.clear_last()
        status = ResultAvro()
        rret_val = None

        try:
            request = ReclaimResourcesAvro()
            request.guid = str(self.management_id)
            request.auth = self.auth
            request.broker_id = str(broker)
            request.delegation_id = did
            request.message_id = str(ID())
            request.callback_topic = self.callback_topic
            request.id_token = id_token

            ret_val = self.producer.produce_sync(topic=self.kafka_topic, record=request)

            self.logger.debug(Constants.management_inter_actor_outbound_message.format(request.name, self.kafka_topic))

            if ret_val:
                message_wrapper = self.message_processor.add_message(message=request)

                with message_wrapper.condition:
                    message_wrapper.condition.wait(Constants.management_api_timeout_in_seconds)

                if not message_wrapper.done:
                    self.logger.debug(Constants.management_api_timeout_occurred)
                    self.message_processor.remove_message(msg_id=request.get_message_id())
                    status.code = ErrorCodes.ErrorTransportTimeout.value
                    status.message = ErrorCodes.ErrorTransportTimeout.name
                else:
                    self.logger.debug(Constants.management_inter_actor_inbound_message.format(message_wrapper.response))
                    status = message_wrapper.response.status
                    if status.code == 0 and message_wrapper.response.delegations is not None and len(
                            message_wrapper.response.delegations) > 0:
                        rret_val = next(iter(message_wrapper.response.delegations))
            else:
                self.logger.debug(Constants.management_inter_actor_message_failed.format(
                    request.name, self.kafka_topic))
                status.code = ErrorCodes.ErrorTransportFailure.value
                status.message = ErrorCodes.ErrorTransportFailure.name
        except Exception as e:
            self.last_exception = e
            status.code = ErrorCodes.ErrorInternalError.value
            status.message = ErrorCodes.ErrorInternalError.name
            status.details = traceback.format_exc()

        self.last_status = status

        return rret_val

    def clone(self):
        return KafkaBroker(guid=self.management_id,
                           kafka_topic=self.kafka_topic,
                           auth=self.auth, logger=self.logger,
                           message_processor=self.message_processor,
                           producer=self.producer)

    def add_broker(self, *, broker: ProxyAvro) -> bool:
        raise ManageException(Constants.not_implemented)
