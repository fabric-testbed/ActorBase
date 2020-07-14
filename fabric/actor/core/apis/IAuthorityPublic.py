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

if TYPE_CHECKING:
    from fabric.actor.core.apis.IControllerCallbackProxy import IControllerCallbackProxy
    from fabric.actor.core.apis.IReservation import IReservation
    from fabric.actor.security.AuthToken import AuthToken


class IAuthorityPublic:
    """
    IAuthorityPublic represents the public cross-actor interface for a site authority.
    """
    def close_by_caller(self, reservation:IReservation, caller: AuthToken):
        """
        Closes the reservation.

        @params reservation:  the reservation
        @params caller : the slice owner

        @raises Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def extend_lease(self, reservation:IReservation, caller: AuthToken):
        """
        Extends a lease.

        @params reservation:  the reservation
        @params caller : the slice owner

        @raises Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def modify_lease(self, reservation:IReservation, caller: AuthToken):
        """
        Modifies a lease.

        @params reservation:  the reservation
        @params caller : the slice owner

        @raises Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def redeem(self, reservation:IReservation, callback: IControllerCallbackProxy, caller: AuthToken):
        """
        Redeems a lease.

        @params reservation:  the reservation
        @params callback: callback
        @params caller : the slice owner

        @raises Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")
