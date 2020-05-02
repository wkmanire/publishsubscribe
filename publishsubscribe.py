"""
A pubsub implementation with features to facilitate game development.
"""

from dataclasses import dataclass, field
from heapq import heappush, heappop, heapify
from logging import getLogger
from threading import Lock
from time import time_ns
from typing import Optional, Any, Set

LOGGER = getLogger(__name__)


@dataclass(order=True)
class Event:
    priority: int = 0
    event_type: int = field(default=0, compare=False)
    data: object = field(default=None, compare=False)


@dataclass(order=True)
class Subscription:
    priority: int = 0
    listener: callable = field(
        default=lambda _: None, compare=False
    )  # pragma: no cover


class PubSubException(Exception):
    pass


LOCK = Lock()
EVENT_QUEUE = list()  # [Event, Event, ...]
SUBSCRIBERS = {"default": dict()}  # {"group_name": {event_type: subscription}}
ACTIVE_GROUP = SUBSCRIBERS["default"]  # {event_type: subscription}


def reset():
    """
    Reset the event system to its initial state.

        1. Clear the event queue

        2. Unsubscribe all subscribers

        3. Delete all subscription groups except for default.
    """
    global EVENT_QUEUE, SUBSCRIBERS, ACTIVE_GROUP
    EVENT_QUEUE = list()
    SUBSCRIBERS = {"default": dict()}
    ACTIVE_GROUP = SUBSCRIBERS["default"]


def subscribe(event_type: int, listener: callable, priority: int = 0):
    global LOCK, ACTIVE_GROUP
    with LOCK:
        LOGGER.debug(f"subscribe: event_type={event_type}, priority={priority}")
        subscription = Subscription(priority, listener)
        if event_type not in ACTIVE_GROUP:
            ACTIVE_GROUP[event_type] = list()
        heappush(ACTIVE_GROUP[event_type], subscription)


def unsubscribe(event_type: int, listener: callable):
    global LOCK, ACTIVE_GROUP
    with LOCK:
        ACTIVE_GROUP[event_type] = [
            s for s in ACTIVE_GROUP[event_type] if s.listener is not listener
        ]


def unsubscribe_all():
    global LOCK, ACTIVE_GROUP
    with LOCK:
        ACTIVE_GROUP = list()


def publish(event_type: int, priority: int = 0, data: Optional[Any] = None):
    global LOCK, EVENT_QUEUE
    with LOCK:
        LOGGER.debug(f"publish: event_type={event_type}, priority={priority}")
        event = Event(priority, event_type, data)
        heappush(EVENT_QUEUE, event)


def create_subscriber_group(group_name: str):
    global LOCK, SUBSCRIBERS
    with LOCK:
        SUBSCRIBERS[group_name] = dict()


def set_active_subscriber_group(group_name: str, flush: bool = False):
    global LOCK, EVENT_QUEUE, ACTIVE_GROUP
    with LOCK:
        # This is duplicated on purpose in order to avoid a race
        # condition and an additional function call. Don't replace
        # with a call to flush!
        if flush:
            LOGGER.debug("flush")
            EVENT_QUEUE = []
        if len(EVENT_QUEUE) != 0:
            raise PubSubException(
                "Attempt to switch subscriber group with non-empty event queue"
            )
        LOGGER.debug(f'set active subscriber group: name="{group_name}"')
        ACTIVE_GROUP = SUBSCRIBERS[group_name]


def dispatch(budget_ms: int = 0, event_types: Optional[Set[int]] = None):
    """
    Remove all events from the queue, notifying their subscribers.

    Optionally, a set of event types, event_types, may be provided.
    Only events that have the specified types will be processed.  The
    remaining events are left in the queue.
    """
    global LOCK, EVENT_QUEUE, ACTIVE_GROUP
    with LOCK:
        LOGGER.debug(f"dispatch: budget={budget_ms}ms")
        if len(EVENT_QUEUE) == 0 or len(ACTIVE_GROUP) == 0:
            return
        budget_ns = budget_ms * 10e6  # convert the budget to nanoseconds
        timestamp = time_ns()
        elapsed_ns = 0
        filtered = list()
        while EVENT_QUEUE and (budget_ms == 0 or elapsed_ns < budget_ns):
            event = heappop(EVENT_QUEUE)
            if event_types and event.event_type not in event_types:
                filtered.append(event)
            else:
                for subscription in ACTIVE_GROUP[event.event_type]:
                    subscription.listener(event.data)
                    elapsed_ns = time_ns() - timestamp
                    if budget_ns > 0 and elapsed_ns >= budget_ns:
                        break
        for event in filtered:
            heappush(EVENT_QUEUE, event)


def flush(event_types: Optional[Set[int]] = None):
    """
    Empty the event queue without dispatching the events.

    Optionally, you may provide a set of event types to flush.  Only
    those types will be removed from the queue.
    """
    global LOCK, EVENT_QUEUE
    LOGGER.debug(f"flush: event_types={event_types}")
    with LOCK:
        if event_types:
            EVENT_QUEUE = [e for e in EVENT_QUEUE if e.event_type not in event_types]
            heapify(EVENT_QUEUE)
        else:
            EVENT_QUEUE = []
