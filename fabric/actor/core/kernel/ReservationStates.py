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
from enum import Enum


class ReservationStates(Enum):
    """
    Reservation states (enum ReservationState) Should be protected: public just for logging
    """
    Nascent = 1
    Ticketed = 2
    Active = 3
    ActiveTicketed = 4
    Closed = 5
    CloseWait = 6
    Failed = 7
    Unknown = 8


class ReservationPendingStates(Enum):
    """
    Pending operation states (enum ReservationPending) Should be protected: public just for logging
    """
    None_ = 1
    Ticketing = 2
    Redeeming = 3
    ExtendingTicket = 4
    ExtendingLease = 5
    Priming = 6
    Blocked = 7
    Closing = 8
    Probing = 9
    ClosingJoining = 10
    ModifyingLease = 11
    AbsorbUpdate = 11
    SendUpdate = 12
    Unknown = 13


class JoinState(Enum):
    None_ = 1
    NoJoin = 2
    BlockedJoin = 3
    BlockedRedeem = 4
    Joining = 5