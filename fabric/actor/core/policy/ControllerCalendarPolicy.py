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
from fabric.actor.core.apis.IClientReservation import IClientReservation
from fabric.actor.core.apis.IControllerPolicy import IControllerPolicy
from fabric.actor.core.apis.IControllerReservation import IControllerReservation
from fabric.actor.core.apis.IReservation import IReservation
from fabric.actor.core.core.Policy import Policy
from fabric.actor.core.kernel.ReservationStates import ReservationStates, ReservationPendingStates
from fabric.actor.core.kernel.ResourceSet import ResourceSet
from fabric.actor.core.time.Term import Term
from fabric.actor.core.time.calendar.ControllerCalendar import ControllerCalendar
from fabric.actor.core.util.ReservationSet import ReservationSet


class ControllerCalendarPolicy(Policy, IControllerPolicy):
    """
    The base class for all calendar-based service manager policy implementations.
    """
    def __init__(self):
        super().__init__()
        # calendar
        self.calendar = None
        # Contains reservations for which we may have completed performing
        # bookkeeping actions but may need to wait for some other event to take
        # place before we raise the corresponding event.
        self.pending_notify = ReservationSet()
        # If the actor is initialized
        self.initialized = False
        # If true, the controller will close reservations lazily: it will not
        # issue a close and will wait until the site terminates the lease. The
        # major drawback is that leave actions will not be able to connect to the
        # resources, since the resources will not exist at this time.
        self.lazy_close = False

    def __getstate__(self):
        state = self.__dict__.copy()
        state['actor_id'] = self.actor.get_reference()
        del state['logger']
        del state['actor']
        del state['clock']
        del state['initialized']
        del state['pending_notify']
        del state['lazy_close']

        return state

    def __setstate__(self, state):
        actor_id = state['actor_id']
        # TODO recover actor
        del state['actor_id']
        self.__dict__.update(state)

        # TODO Fetch Actor object and setup logger, actor and clock member variables

    def check_pending(self):
        """
        Checks pending operations, and installs successfully completed
        requests in the holdings calendar. Note that the policy module must add
        bids to the pending set, or they may not install in the calendar.
       
        @raises Exception in case of error
        """
        rvset = self.calendar.get_pending()
        if rvset is None:
            return

        for reservation in rvset.values():
            if reservation.is_failed():
                # This reservation has failed. Remove it from the list. This is
                # a separate case, because we may fail but not satisfy the
                # condition of the else statement.
                self.logger.debug("Removing failed reservation from the pending list: {}".format(reservation))
                self.calendar.remove_pending(reservation)
                self.pending_notify.remove(reservation)
            elif reservation.is_no_pending() and not reservation.is_pending_recover():
                # No pending operation and we are not about the reissue a recovery operation on this reservation.
                self.logger.debug("Controller pending request completed {}".format(reservation))
                if reservation.get_state() == ReservationStates.Closed.value:
                    # do nothing handled by close(IReservation)
                    self.logger.debug("No op")
                elif reservation.is_active_ticketed():
                    # An active reservation extended its ticket.
                    # cancel the current close
                    self.calendar.remove_closing(reservation)
                    # schedule a new close
                    self.calendar.add_closing(reservation, self.get_close(reservation, reservation.get_term()))
                    # Add from start to end instead of close. It is possible
                    # that holdings may not accurately reflect the actual
                    # number of resources towards the end of a lease. This is
                    # because we assume that we still have resources even after
                    # an advanceClose. When looking at this value, see if the
                    # reservation has closed.
                    self.calendar.add_holdings(reservation, reservation.get_term().get_new_start_time(),
                                               reservation.get_term().get_end_time())
                    self.calendar.add_redeeming(reservation, self.get_redeem(reservation))
                    if reservation.is_renewable():
                        cycle = self.get_renew(reservation)
                        reservation.set_renew_time(cycle)
                        reservation.set_dirty()
                        self.calendar.add_renewing(reservation, cycle)
                    self.pending_notify.remove(reservation)
                elif reservation.is_ticketed():
                    # The reservation obtained a ticket for the first time
                    self.calendar.add_holdings(reservation, reservation.get_term().get_new_start_time(),
                                               reservation.get_term().get_end_time())
                    self.calendar.add_redeeming(reservation, self.get_redeem(reservation))
                    self.calendar.add_closing(reservation, self.get_close(reservation, reservation.get_term()))
                    if reservation.is_renewable():
                        cycle = self.get_renew(reservation)
                        reservation.set_renew_time(cycle)
                        reservation.set_dirty()
                        self.calendar.add_renewing(reservation, cycle)
                    self.pending_notify.remove(reservation)
                elif reservation.get_state() == ReservationStates.Active:
                    if self.pending_notify.contains(reservation):
                        # We are waiting for transfer in operations to complete
                        # so that we can raise the lease complete event.
                        if reservation.is_active_joined():
                            self.pending_notify.remove(reservation)
                    else:
                        # Just completed a lease call (redeem or extendLease).
                        # We need to remove this reservation from closing,
                        # because we added it using r.getTerm(), and add this
                        # reservation to closing using r.getLeasedTerm() [the
                        # site could have changed the term of the reservation].
                        # This assumes that r.getTerm has not changed in the
                        # mean time. This is true now, since the state machine
                        # does not allow more than one pending operation.
                        # Should we change this, we will need to update the
                        # code below.
                        self.calendar.remove_closing(reservation)
                        self.calendar.add_closing(reservation, self.get_close(reservation, reservation.get_lease_term()))
                        if reservation.get_renew_time() == 0:
                            reservation.set_renew_time(self.actor.get_current_cycle() + 1)
                            reservation.set_dirty()
                            self.calendar.add_renewing(reservation, reservation.get_renew_time())

                    if not reservation.is_active_joined():
                        # add to the pending notify list so that we can raise the event
                        # when transfer in operations complete.
                        self.pending_notify.add(reservation)
                elif reservation.get_state() == ReservationStates.CloseWait or \
                        reservation.get_state() == ReservationStates.Failed:
                    self.pending_notify.remove(reservation)
                else:
                    self.logger.warning("Invalid state on reservation. We may be still recovering: {}".format(reservation))
                    continue

                if self.pending_notify.contains(reservation):
                    self.logger.debug("Removing from pending: {}".format(reservation))
                    self.calendar.remove_pending(reservation)

    def close(self, reservation:IReservation):
        # ignore any scheduled/in progress operations
        self.calendar.remove_scheduled_or_in_progress(reservation)

    def closed(self, reservation: IReservation):
        # remove the reservation from all calendar structures
        self.calendar.remove_holdings(reservation)
        self.calendar.remove_redeeming(reservation)
        self.calendar.remove_renewing(reservation)
        self.calendar.remove_closing(reservation)
        self.pending_notify.remove(reservation)

    def demand(self, reservation: IClientReservation):
        if not reservation.is_nascent():
            self.logger.error("demand reservation is not fresh")
        else:
            self.calendar.add_demand(reservation)

    def extend(self, reservation: IReservation, resources: ResourceSet, term: Term):
        # cancel any previously scheduled extends
        self.calendar.remove_renewing(reservation)
        # do not cancel the close: the extend may fail cancel any pending redeem: we will redeem after the extension
        self.calendar.remove_redeeming(reservation)
        # There should be no pending operations for this reservation at this time
        # Add to the pending list so that we can track the progress of the reservation
        self.calendar.add_pending(reservation)

    def finish(self, cycle: int):
        super().finish(cycle)
        self.calendar.tick(cycle)

    def get_close(self, reservation: IClientReservation, term: Term) -> int:
        """
        Returns the time that a reservation should be closed.
       
        @params reservation reservation
        @params term term
       
        @returns the close time of the reservation (cycle)
       
        @raises Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def get_closing(self, cycle: int) -> ReservationSet:
        closing = self.calendar.get_closing(cycle)
        result = ReservationSet()
        for reservation in closing.values():
            if not reservation.is_failed():
                self.calendar.add_pending(reservation)
                result.add(reservation)
            else:
                self.logger.warning("Removing failed reservation from the closing list: {}".format(reservation))
        return result

    def get_redeem(self, reservation: IClientReservation) -> int:
        """
        Returns the time when the reservation should be redeemed.
       
        @params reservation the reservation
       
        @returns the redeem time of the reservation (cycle)
       
        @raises Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def get_redeeming(self, cycle: int) -> ReservationSet:
        redeeming = self.calendar.get_redeeming(cycle)
        for reservation in redeeming.values():
            if reservation.is_active_ticketed():
                self.calendar.add_pending(reservation)
            else:
                self.calendar.add_pending(reservation)
        return redeeming

    def get_renew(self, reservation: IClientReservation) -> int:
        """
        Returns the time when the reservation should be renewed.
       
        @params reservation the reservation
       
        @returns the renew time of the reservation (cycle)
       
        @raises Exception in case of error
        """
        raise NotImplementedError("Should have implemented this")

    def initialize(self):
        if not self.initialized:
            super().initialize()
            self.calendar = ControllerCalendar(self.clock)
            self.initialized = True

    def is_expired(self, reservation:IReservation):
        """
        Checks if the reservation has expired.
       
        @params reservation reservation to check
       
        @returns true or false
        """
        term = reservation.get_term()
        end = self.clock.cycle(when=term.get_end_time())
        return self.actor.get_current_cycle() > end

    def remove(self, reservation: IReservation):
        # remove the reservation from the calendar
        self.calendar.remove(reservation)

    def revisit(self, reservation: IReservation):
        super().revisit(reservation)

        if reservation.get_state() == ReservationStates.Nascent:
            self.calendar.add_pending(reservation)

        elif reservation.get_state() == ReservationStates.Ticketed:

            if reservation.get_pending_state() == ReservationPendingStates.None_:

                if reservation.is_pending_recover():

                    self.calendar.add_pending(reservation)

                else:

                    self.calendar.add_redeeming(reservation, self.get_redeem(reservation))

                self.calendar.add_holdings(reservation, reservation.get_term().get_new_start_time(),
                                           reservation.get_term().get_end_time())

                self.calendar.add_closing(reservation, self.get_close(reservation, reservation.get_term()))

                if reservation.is_renewable():
                    # Scheduling renewal is a bit tricky, since it may
                    # involve communication with the upstream broker.
                    # However, in some recovery cases, typical in one
                    # container deployment, the broker and the service
                    # manager will be recovering at the same time. In
                    # this case the query may fail and we will have to
                    # fail the reservation.
                    # Our approach here is as follows: we cache the
                    # renew time in the reservation class and persist
                    # it in the database. When we recover, we will
                    # check the renewTime field of the reservation if
                    # it is non-zero, we will use it, otherwise we will
                    # schedule the renew after we get the lease back
                    # from the authority.
                    if reservation.get_renew_time() != 0:
                        self.calendar.add_renewing(reservation, reservation.get_renew_time())

            elif reservation.get_pending_state() == ReservationPendingStates.Redeeming:
                raise Exception("This state should not be reached during recovery")

        elif reservation.get_state() == ReservationStates.Active:
            if reservation.get_pending_state() == ReservationPendingStates.None_:
                # pending list
                if reservation.is_pending_recover():
                    self.calendar.add_pending(reservation)
                # renewing
                if reservation.is_renewable():
                    self.calendar.add_renewing(reservation, reservation.get_renew_time())
                # holdings
                self.calendar.add_holdings(reservation, reservation.get_term().get_new_start_time(),
                                           reservation.get_term().get_end_time())
                # closing
                self.calendar.add_closing(reservation, self.get_close(reservation, reservation.get_lease_term()))

            elif reservation.get_pending_state() == ReservationPendingStates.ExtendingTicket:
                raise Exception("This state should not be reached during recovery")

        elif reservation.get_state() == ReservationStates.ActiveTicketed:

            if reservation.get_pending_state() == ReservationPendingStates.None_:
                if reservation.is_pending_recover():
                    self.calendar.add_pending(reservation)
                else:
                    self.calendar.add_redeeming(reservation, self.get_redeem(reservation))

                # holdings
                self.calendar.add_holdings(reservation, reservation.get_term().get_new_start_time(),
                                           reservation.get_term().get_end_time())

                # closing
                self.calendar.add_closing(reservation,
                                          self.get_close(reservation, reservation.get_lease_term()))

                # renewing
                if reservation.is_renewable():
                    self.calendar.add_renewing(reservation, reservation.get_renew_time())

            elif reservation.get_pending_state() == ReservationPendingStates.ExtendingLease:
                raise Exception("This state should not be reached during recovery")