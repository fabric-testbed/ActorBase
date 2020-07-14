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

from fabric.actor.core.apis.IAuthority import IAuthority
from fabric.actor.core.apis.IBroker import IBroker
from fabric.actor.core.proxies.local.LocalAuthority import LocalAuthority
from fabric.actor.core.proxies.local.LocalBroker import LocalBroker
from fabric.actor.core.proxies.local.LocalReturn import LocalReturn
from fabric.actor.core.registry.ActorRegistry import ActorRegistrySingleton

if TYPE_CHECKING:
    from fabric.actor.core.apis.IActorIdentity import IActorIdentity
    from fabric.actor.core.proxies.ActorLocation import ActorLocation
    from fabric.actor.core.apis.ICallbackProxy import ICallbackProxy
    from fabric.actor.core.apis.IProxy import IProxy

from fabric.actor.core.proxies.IProxyFactory import IProxyFactory


class LocalProxyFactory(IProxyFactory):
    def new_callback(self, identity: IActorIdentity, location: ActorLocation) -> ICallbackProxy:
        actor = ActorRegistrySingleton.get().get_actor(identity.get_name())
        if actor is not None:
            return LocalReturn(actor)
        return None

    def new_proxy(self, identity: IActorIdentity, location: ActorLocation, type: str = None) -> IProxy:
        actor = ActorRegistrySingleton.get().get_actor(identity.get_name())
        if actor is not None:
            if isinstance(actor, IAuthority):
                return LocalAuthority(actor)
            elif isinstance(actor, IBroker):
                return LocalBroker(actor)
        return None
