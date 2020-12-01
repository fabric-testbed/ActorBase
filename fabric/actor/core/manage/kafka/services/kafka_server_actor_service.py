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

from fabric.actor.core.apis.i_reservation import ReservationCategory
from fabric.actor.core.common.constants import ErrorCodes
from fabric.actor.core.kernel.slice import SliceTypes
from fabric.actor.core.manage.kafka.services.kafka_actor_service import KafkaActorService
from fabric.actor.core.manage.management_object import ManagementObject
from fabric.actor.core.proxies.kafka.translate import Translate
from fabric.actor.core.util.id import ID
from fabric.message_bus.messages.add_slice_avro import AddSliceAvro
from fabric.message_bus.messages.get_reservations_request_avro import GetReservationsRequestAvro
from fabric.message_bus.messages.get_slices_request_avro import GetSlicesRequestAvro
from fabric.message_bus.messages.message import IMessageAvro
from fabric.message_bus.messages.result_avro import ResultAvro
from fabric.message_bus.messages.result_reservation_avro import ResultReservationAvro
from fabric.message_bus.messages.result_slice_avro import ResultSliceAvro
from fabric.message_bus.messages.result_string_avro import ResultStringAvro


class KafkaServerActorService(KafkaActorService):
    def __init__(self):
        super().__init__()

    def process(self, *, message: IMessageAvro):
        callback_topic = message.get_callback_topic()
        result = None

        self.logger.debug("Processing message: {}".format(message.get_message_name()))

        if message.get_message_name() == IMessageAvro.GetReservationsRequest and \
                message.get_reservation_type() is not None and \
                message.get_reservation_type() == ReservationCategory.Broker.name:
            result = self.get_reservations_by_category(request=message, category=ReservationCategory.Broker)
        elif message.get_message_name() == IMessageAvro.GetSlicesRequest and \
                message.get_slice_type() is not None and \
                message.get_slice_type() == SliceTypes.InventorySlice.name:
            result = self.get_slices_by_slice_type(request=message, slice_type=SliceTypes.InventorySlice)
        elif message.get_message_name() == IMessageAvro.GetReservationsRequest and \
                message.get_reservation_type() is not None and \
                message.get_reservation_type() == ReservationCategory.Client.name:
            result = self.get_reservations_by_category(request=message, category=ReservationCategory.Inventory)
        elif message.get_message_name() == IMessageAvro.GetSlicesRequest and \
                message.get_slice_type() is not None and \
                message.get_slice_type() == SliceTypes.ClientSlice.name:
            result = self.get_slices_by_slice_type(request=message, slice_type=SliceTypes.ClientSlice)
        elif message.get_message_name() == IMessageAvro.AddSlice and message.slice_obj is not None and \
                (message.slice_obj.is_client_slice() or message.slice_obj.is_broker_client_slice()):
            result = self.add_client_slice(request=message)
        else:
            super().process(message=message)
            return

        if callback_topic is None:
            self.logger.debug("No callback specified, ignoring the message")

        if self.producer.produce_sync(callback_topic, result):
            self.logger.debug("Successfully send back response: {}".format(result.to_dict()))
        else:
            self.logger.debug("Failed to send back response: {}".format(result.to_dict()))

    def get_reservations_by_category(self, *, request: GetReservationsRequestAvro,
                                     category: ReservationCategory) -> ResultReservationAvro:
        result = ResultReservationAvro()
        result.status = ResultAvro()
        try:
            if request.guid is None:
                result.status.set_code(ErrorCodes.ErrorInvalidArguments.value)
                result.status.set_message(ErrorCodes.ErrorInvalidArguments.name)
                return result

            auth = Translate.translate_auth_from_avro(auth_avro=request.auth)
            mo = self.get_actor_mo(guid=ID(id=request.guid))

            result = mo.get_reservations_by_category(caller=auth, category=category, id_token=request.get_id_token(),
                                                     slice_id=request.slice_id)
            result.message_id = request.message_id

        except Exception as e:
            result.status.set_code(ErrorCodes.ErrorInternalError.value)
            result.status.set_message(ErrorCodes.ErrorInternalError.name)
            result.status = ManagementObject.set_exception_details(result=result.status, e=e)

        return result

    def get_slices_by_slice_type(self, *, request: GetSlicesRequestAvro, slice_type: SliceTypes) -> ResultSliceAvro:
        result = ResultSliceAvro()
        result.status = ResultAvro()
        try:
            if request.guid is None:
                result.status.set_code(ErrorCodes.ErrorInvalidArguments.value)
                result.status.set_message(ErrorCodes.ErrorInvalidArguments.name)
                return result

            auth = Translate.translate_auth_from_avro(auth_avro=request.auth)
            mo = self.get_actor_mo(guid=ID(id=request.guid))

            result = mo.get_slices_by_slice_type(caller=auth, slice_type=slice_type, id_token=request.get_id_token())
            result.message_id = request.message_id

        except Exception as e:
            result.status.set_code(ErrorCodes.ErrorInternalError.value)
            result.status.set_message(ErrorCodes.ErrorInternalError.name)
            result.status = ManagementObject.set_exception_details(result=result.status, e=e)

        return result

    def add_client_slice(self, *, request: AddSliceAvro) -> ResultStringAvro:
        result = ResultStringAvro()
        result.status = ResultAvro()

        try:
            if request.guid is None:
                result.status.set_code(ErrorCodes.ErrorInvalidArguments.value)
                result.status.set_message(ErrorCodes.ErrorInvalidArguments.name)
                return result

            auth = Translate.translate_auth_from_avro(auth_avro=request.auth)
            mo = self.get_actor_mo(guid=ID(id=request.guid))

            result = mo.add_client_slice(caller=auth, slice_obj=request.slice_obj)
            result.message_id = request.message_id

        except Exception as e:
            result.status.set_code(ErrorCodes.ErrorInternalError.value)
            result.status.set_message(ErrorCodes.ErrorInternalError.name)
            result.status = ManagementObject.set_exception_details(result=result.status, e=e)

        return result
