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

from fabric.actor.core.proxies.kafka.Translate import Translate
from fabric.message_bus.messages.FailedRPCAvro import FailedRPCAvro
from fabric.message_bus.messages.QueryAvro import QueryAvro
from fabric.message_bus.messages.QueryResultAvro import QueryResultAvro
from fabric.message_bus.producer import AvroProducerApi

if TYPE_CHECKING:
    from fabric.actor.core.apis.IRPCRequestState import IRPCRequestState
    from fabric.actor.security.AuthToken import AuthToken
    from fabric.actor.core.util.ID import ID

from fabric.actor.core.apis.ICallbackProxy import ICallbackProxy
from fabric.actor.core.common.Constants import Constants
from fabric.actor.core.core.RPCRequestState import RPCRequestState
from fabric.actor.core.kernel.RPCRequestType import RPCRequestType
from fabric.actor.core.proxies.Proxy import Proxy


class KafkaProxyRequestState(RPCRequestState):
    def __init__(self):
        super().__init__()
        self.callback_topic = None
        self.reservation = None
        self.udd = None
        self.query = None
        self.request_id = None
        self.failed_reservation_id = None
        self.failed_request_type = None
        self.error_detail = None


class KafkaProxy(Proxy, ICallbackProxy):
    TypeDefault = 0
    TypeReturn = 1
    TypeBroker = 2
    TypeSite = 3

    def __init__(self, kafka_topic: str, identity: AuthToken, logger):
        super().__init__(identity)
        self.kafka_topic = kafka_topic
        self.logger = logger
        self.proxy_type = Constants.ProtocolKafka
        self.type = self.TypeDefault

        from fabric.actor.core.container.Globals import GlobalsSingleton
        config = GlobalsSingleton.get().get_config()
        self.bootstrap_server = config.get_global_config().get_runtime()[Constants.PropertyConfKafkaServer]

        self.schema_registry = config.get_global_config().get_runtime()[Constants.PropertyConfKafkaSchemaRegistry]

        self.key_schema_file = config.get_global_config().get_runtime()[Constants.PropertyConfKafkaKeySchema]

        self.value_schema_file = config.get_global_config().get_runtime()[Constants.PropertyConfKafkaValueSchema]

        self.producer = self.create_kafka_producer()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['logger']
        del state['producer']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.logger = None
        self.producer = self.create_kafka_producer()

    def create_kafka_producer(self) -> AvroProducerApi:
        from confluent_kafka import avro
        conf = {'bootstrap.servers': self.bootstrap_server,
                     'schema.registry.url': self.schema_registry}

        file = open(self.key_schema_file, "r")
        kbytes = file.read()
        file.close()
        key_schema = avro.loads(kbytes)
        file = open(self.value_schema_file, "r")
        vbytes = file.read()
        file.close()
        val_schema = avro.loads(vbytes)

        # create a producer
        return AvroProducerApi(conf, key_schema, val_schema, self.logger)

    def execute(self, request: IRPCRequestState):
        avro_message = None
        if request.get_type() == RPCRequestType.Query:
            avro_message = QueryAvro()
            avro_message.message_id = str(request.get_message_id())
            avro_message.properties = request.query
            avro_message.callback_topic = request.callback_topic
            avro_message.auth = Translate.translate_auth_to_avro(request.caller)

        elif request.get_type() == RPCRequestType.QueryResult:
            avro_message = QueryResultAvro()
            avro_message.message_id = str(request.get_message_id())
            avro_message.request_id = str(request.request_id)
            avro_message.properties = request.query
            avro_message.auth = Translate.translate_auth_to_avro(request.caller)

        elif request.get_type() == RPCRequestType.FailedRPC:
            avro_message = FailedRPCAvro()
            avro_message.message_id = str(request.get_message_id())
            avro_message.request_id = str(request.request_id)
            avro_message.request_type = request.failed_request_type.value
            avro_message.auth = Translate.translate_auth_to_avro(request.caller)

            if request.failed_reservation_id is not None:
                avro_message.reservation_id = request.failed_reservation_id
            else:
                avro_message.reservation_id = ""
            avro_message.error_details = request.error_details

        else:
            raise Exception("Unsupported RPC: type={}".format(request.get_type()))

        if self.producer.produce_sync(self.kafka_topic, avro_message):
            self.logger.debug("Message {} written to {}".format(avro_message.name, self.kafka_topic))
        else:
            self.logger.error("Failed to send message {} to {}".format(avro_message.name, self.kafka_topic))

    def prepare_query(self, callback: ICallbackProxy, query: dict, caller: AuthToken):
        request = KafkaProxyRequestState()
        request.query = query
        request.callback_topic = callback.get_kafka_topic()
        request.caller = caller
        return request

    def prepare_query_result(self, request_id: str, response, caller: AuthToken) -> IRPCRequestState:
        request = KafkaProxyRequestState()
        request.query = response
        request.request_id = request_id
        request.caller = caller
        return request

    def prepare_failed_request(self, request_id: str, failed_request_type,
                               failed_reservation_id: ID, error: str, caller: AuthToken) -> IRPCRequestState:
        request = KafkaProxyRequestState()
        request.failed_request_type = failed_request_type
        request.failed_reservation_id = failed_reservation_id
        request.error_detail = error
        request.request_id = request_id
        request.caller = caller
        return request

    def get_kafka_topic(self):
        return self.kafka_topic