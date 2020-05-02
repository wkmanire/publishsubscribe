import logging
import pytest
from time import sleep

from publishsubscribe import (
    PubSubException,
    create_subscriber_group,
    dispatch,
    flush,
    publish,
    reset,
    set_active_subscriber_group,
    subscribe,
    unsubscribe,
    unsubscribe_all,
)


def test_subcribe_publish_dispatch():
    reset()
    called1 = False
    called2 = False

    def callback1(data):
        nonlocal called1
        called1 = True

    def callback2(data):
        nonlocal called2
        called2 = True

    event_type = 1
    subscribe(event_type, callback1)
    subscribe(event_type, callback2)
    publish(event_type)
    assert not (called1 or called2)
    dispatch()
    assert called1 and called2


def test_create_subscriber_group():
    reset()
    called = False

    def callback(data):
        nonlocal called
        called = True

    event_type = 1
    subscribe(event_type, callback)
    create_subscriber_group("test")
    set_active_subscriber_group("test")
    publish(event_type)
    dispatch()

    assert not called


def test_set_group_with_non_empty_queue_raises():
    reset()
    event_type = 1
    subscribe(event_type, lambda _: None)
    publish(event_type)
    create_subscriber_group("test")

    with pytest.raises(PubSubException) as ex:
        set_active_subscriber_group("test")
    assert "non-empty event queue" in str(ex)

    flush()
    set_active_subscriber_group("test")
    publish(event_type)
    set_active_subscriber_group("test", flush=True)


def test_flush():
    reset()
    called1 = False
    called2 = False

    def callback1(data):
        nonlocal called1
        called1 = True

    def callback2(data):
        nonlocal called2
        called2 = True

    event_type_1 = 1
    event_type_2 = 2
    subscribe(event_type_1, callback1)
    subscribe(event_type_2, callback2)
    publish(event_type_1)
    publish(event_type_2)
    assert not (called1 or called2)
    flush({2})
    dispatch()
    assert called1
    assert not called2


def test_unsubscribe():
    reset()
    called = False

    def callback(data):
        nonlocal called
        called = True

    event_type = 1
    subscribe(event_type, callback)
    unsubscribe(event_type, callback)
    publish(event_type)
    dispatch()
    assert not called


def test_dispatch_budget():
    reset()
    called1 = False
    called2 = False

    def callback1(data):
        nonlocal called1
        sleep(0.01)  # sleep for 100ms
        called1 = True

    def callback2(data):
        nonlocal called2
        called2 = True

    event_type = 1
    subscribe(event_type, callback1)
    subscribe(event_type, callback2)
    publish(event_type)
    assert not (called1 or called2)
    dispatch(budget_ms=1)
    assert called1
    assert not called2


def test_dispatch_by_event_type():
    reset()
    called1 = False
    called2 = False

    def callback1(data):
        nonlocal called1
        called1 = True

    def callback2(data):
        nonlocal called2
        called2 = True

    event_type_1 = 1
    event_type_2 = 2
    subscribe(event_type_1, callback1)
    subscribe(event_type_2, callback2)
    publish(event_type_1)
    publish(event_type_2)
    assert not (called1 or called2)
    dispatch(event_types={event_type_1})
    assert called1
    assert not called2
    dispatch(event_types={event_type_2})
    assert called2


def test_unsubscribe_all():
    reset()
    called1 = False
    called2 = False

    def callback1(data):
        nonlocal called1
        called1 = True

    def callback2(data):
        nonlocal called2
        called2 = True

    event_type = 1
    subscribe(event_type, callback1)
    subscribe(event_type, callback2)
    unsubscribe_all()
    publish(event_type)
    assert not (called1 or called2)
    dispatch()


def test_subscriber_prioritization():
    reset()
    call_order = list()

    def callback1(data):
        nonlocal call_order
        call_order.append("callback1")

    def callback2(data):
        nonlocal call_order
        call_order.append("callback2")

    event_type = 1
    high_priority = 1
    low_priority = 2
    subscribe(event_type, callback1, low_priority)
    subscribe(event_type, callback2, high_priority)
    publish(event_type)
    assert call_order == []
    dispatch()
    assert call_order == ["callback2", "callback1"]


def test_message_prioritization():
    reset()
    event_order = list()

    def callback(data):
        nonlocal event_order
        event_order.append(data)

    event_type = 1
    subscribe(event_type, callback)
    high_priority = 1
    low_priority = 2

    # the low priority event is published before the high priority event
    publish(event_type, priority=low_priority, data="low_priority")
    publish(event_type, priority=high_priority, data="high_priority")
    dispatch()

    # but we expect to see the high priority event dispatched before
    # the lower priority event
    assert event_order == ["high_priority", "low_priority"]
