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
from datetime import datetime

from fabric.actor.core.common.Constants import Constants


class GlobalConfig:
    def __init__(self, config: dict):
        self.runtime = {}
        if Constants.ConfigSectionRuntime in config:
            for prop in config[Constants.ConfigSectionRuntime]:
                for key, value in prop.items():
                    self.runtime[key] = value
        self.logging = {}
        if Constants.ConfigLoggingSection in config:
            for prop in config[Constants.ConfigLoggingSection]:
                for key, value in prop.items():
                    self.logging[key] = value
        self.oauth = {}
        if Constants.ConfigSectionOAuth in config:
            for prop in config[Constants.ConfigSectionOAuth]:
                for key, value in prop.items():
                    self.oauth[key] = value
        self.database = {}
        if Constants.ConfigSectionDatabase in config:
            for prop in config[Constants.ConfigSectionDatabase]:
                for key, value in prop.items():
                    self.database[key] = value
        self.container = {}
        if Constants.ConfigSectionContainer in config:
            for prop in config[Constants.ConfigSectionContainer]:
                for key, value in prop.items():
                    self.container[key] = value
        self.time = {}
        if Constants.ConfigSectionTime in config:
            for prop in config[Constants.ConfigSectionTime]:
                for key, value in prop.items():
                    self.time[key] = value

    def get_runtime(self) -> dict:
        return self.runtime

    def get_logging(self) -> dict:
        return self.logging

    def get_oauth(self) -> dict:
        return self.oauth

    def get_database(self) -> dict:
        return self.database

    def get_container(self) -> dict:
        return self.container

    def get_time(self) -> dict:
        return self.time


class HandlerConfig:
    def __init__(self, config: list):
        self.module_name = None
        self.class_name = None
        self.properties = {}
        for prop in config:
            for key, value in prop.items():
                if key == 'module':
                    self.module_name = value
                elif key == 'class_name':
                    self.class_name = value
                elif key == 'properties':
                    for p in value:
                        for k, v in p.items():
                            self.properties[k] = str(v)

    def get_module_name(self) -> str:
        return self.module_name

    def get_class_name(self) -> str:
        return self.class_name

    def get_properties(self) -> dict:
        return self.properties


class Attribute:
    def __init__(self, config: list):
        self.key = None
        self.type = None
        self.value = None
        for prop in config:
            for key, value in prop.items():
                if key == 'key':
                    self.key = value
                elif key == 'type':
                    self.type = value
                elif key == 'value':
                    self.value = value

    def get_type(self) -> str:
        return self.type

    def get_key(self) -> str:
        return self.key

    def get_value(self) -> str:
        return self.value


class PoolConfig:
    def __init__(self, config: list):
        self.description = None
        self.attributes = []
        self.type = None
        self.label = None
        self.units = None
        now = datetime.utcnow()
        self.start = now
        self.end = now.replace(year=now.year + 20)
        self.properties = {}
        self.factory_module = None
        self.factory_class = None
        self.handler = None
        for prop in config:
            for key, value in prop.items():
                if key == 'type':
                    self.type = value
                elif key == 'label':
                    self.label = value
                elif key == 'description':
                    self.description = value
                elif key == 'units':
                    self.units = int(value)
                elif key == 'start':
                    self.start = value
                elif key == 'end':
                    self.end = value
                elif key == 'properties':
                    for p in value:
                        for k, v in p.items():
                            self.properties[k] = str(v)
                elif key == 'factory.class':
                    self.factory_class = value
                elif key == 'factory.module':
                    self.factory_module = value
                elif key == 'handler':
                    self.handler = HandlerConfig(value)
                elif key == 'attributes':
                    for a in value:
                        self.attributes.append(Attribute(a['attribute']))

    def get_type(self) -> str:
        return self.type

    def get_label(self) -> str:
        return self.label

    def get_description(self) -> str:
        return self.description

    def get_units(self) -> int:
        return self.units

    def get_start(self) -> datetime:
        return self.start

    def get_end(self) -> datetime:
        return self.end

    def get_handler(self) -> HandlerConfig:
        return self.handler

    def get_properties(self) -> dict:
        return self.properties

    def get_factory_class(self) -> str:
        return self.factory_class

    def get_factory_module(self) -> str:
        return self.factory_module

    def get_attributes(self) -> list:
        return self.attributes


class ControlConfig:
    def __init__(self, config: list):
        self.type = None
        self.module_name = None
        self.class_name = None
        for prop in config:
            for key, value in prop.items():
                if key == 'type':
                    self.type = value
                elif key == 'module':
                    self.module_name = value
                elif key == 'class':
                    self.class_name = value

    def get_type(self) -> str:
        return self.type

    def get_module_name(self) -> str:
        return self.module_name

    def get_class_name(self) -> str:
        return self.class_name


class PolicyConfig:
    def __init__(self, config: list):
        self.module_name = None
        self.class_name = None
        self.properties = {}
        for prop in config:
            for key, value in prop.items():
                if key == 'module':
                    self.module_name = value
                elif key == 'class':
                    self.class_name = value
                elif key == 'properties':
                    for p in value:
                        for k, v in p.items():
                            self.properties[k] = str(v)

    def get_module_name(self) -> str:
        return self.module_name

    def get_class_name(self) -> str:
        return self.class_name

    def get_properties(self) -> dict:
        return self.properties


class ActorConfig:
    def __init__(self, config: list):
        self.policy = None
        self.description = None
        self.pools = []
        self.controls = []
        self.type = None
        self.name = None
        self.guid = None
        self.kafka_topic = None
        self.policy = None
        for prop in config:
            for key, value in prop.items():
                if key == 'type':
                    self.type = value
                elif key == 'name':
                    self.name = value
                elif key == 'guid':
                    self.guid = value
                elif key == 'description':
                    self.description = value
                elif key == 'kafka-topic':
                    self.kafka_topic = value
                elif key == 'pools':
                    for p in value:
                        self.pools.append(PoolConfig(p['pool']))
                elif key == 'controls':
                    for c in value:
                        self.controls.append(ControlConfig(c['control']))
                elif key == 'policy':
                    self.policy = PolicyConfig(value)

    def get_type(self) -> str:
        return self.type

    def get_name(self) -> str:
        return self.name

    def get_guid(self) -> str:
        return self.guid

    def get_description(self) -> str:
        return self.description

    def get_kafka_topic(self) -> str:
        return self.kafka_topic

    def get_pools(self) -> list:
        return self.pools

    def get_controls(self) -> list:
        return self.controls

    def get_policy(self) -> PolicyConfig:
        return self.policy


class RsetConfig:
    def __init__(self, config: list):
        self.type = None
        self.units = None
        now = datetime.utcnow()
        self.start = now
        self.end = now.replace(year=now.year + 20)
        for prop in config:
            for key, value in prop.items():
                if key == 'type':
                    self.type = value
                elif key == 'units':
                    self.units = int(value)
                elif key == 'start':
                    self.start = value
                elif key == 'end':
                    self.end = value

    def get_type(self) -> str:
        return self.type

    def get_units(self) -> int:
        return self.units

    def get_start(self) -> datetime:
        return self.start

    def get_end(self) -> datetime:
        return self.end


class Peer:
    def __init__(self, config: list):
        self.name = None
        self.type = None
        self.guid = None
        self.kafka_topic = None
        self.rsets = []
        for prop in config:
            for key, value in prop.items():
                if key == 'name':
                    self.name = value
                elif key == 'type':
                    self.type = value
                elif key == 'guid':
                    self.guid = value
                elif key == 'kafka-topic':
                    self.kafka_topic = value
                elif key == 'rsets':
                    for r in value:
                        self.rsets.append(RsetConfig(r['rset']))

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> str:
        return self.type

    def get_guid(self) -> str:
        return self.guid

    def get_kafka_topic(self) -> str:
        return self.kafka_topic

    def get_rsets(self) -> list:
        return self.rsets


class Configuration:
    def __init__(self, config: dict):
        self.global_config = GlobalConfig(config)
        self.actor = ActorConfig(config['actor'])
        self.peers = []
        if 'peers' in config:
            for e in config['peers']:
                self.peers.append(Peer(e['peer']))

    def get_global_config(self) -> GlobalConfig:
        return self.global_config

    def get_actor(self) -> ActorConfig:
        return self.actor

    def get_peers(self) -> list:
        return self.peers
