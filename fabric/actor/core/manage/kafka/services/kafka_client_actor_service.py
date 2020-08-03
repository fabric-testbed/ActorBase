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

from fabric.actor.core.common.constants import ErrorCodes
from fabric.actor.core.manage.kafka.services.kafka_actor_service import KafkaActorService
from fabric.actor.core.proxies.kafka.translate import Translate
from fabric.message_bus.messages.claim_resources_avro import ClaimResourcesAvro
from fabric.actor.core.util.id import ID
from fabric.message_bus.messages.result_avro import ResultAvro
from fabric.message_bus.messages.result_reservation_avro import ResultReservationAvro


class KafkaClientActorService(KafkaActorService):
    def __init__(self):
        super().__init__()

    def claim_resources(self, request: ClaimResourcesAvro) -> ResultReservationAvro:
        result = ResultReservationAvro()
        result.status = ResultAvro()
        try:
            if request.guid is None or request.broker_id is None or request.reservation_id is None:
                result.status.set_code(ErrorCodes.ErrorInvalidArguments.value)
                result.status.set_message(ErrorCodes.ErrorInvalidArguments.name)
                return result

            auth = Translate.translate_auth_from_avro(request.auth)
            mo = self.get_actor_mo(ID(request.guid))

            if mo is None:
                print("Management object could not be found: guid: {} auth: {}".format(request.guid, auth))
                result.status.set_code(ErrorCodes.ErrorNoSuchBroker.value)
                result.status.set_message(ErrorCodes.ErrorNoSuchBroker.name)
                return result

            if request.slice_id is not None:
                result = mo.claim_resources_slice(ID(request.broker_id), ID(request.slice_id), ID(request.reservation_id), auth)
            else:
                result = mo.claim_resources(ID(request.broker_id), ID(request.reservation_id), auth)

            result.message_id = request.message_id

        except Exception as e:
            result.status.set_code(ErrorCodes.ErrorInvalidArguments.value)
            result.status.set_message(ErrorCodes.ErrorInvalidArguments.name)
            result.status.set_message(str(e))
            result.status.set_details(traceback.format_exc())

        return result

