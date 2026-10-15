# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""What B-AAC's Profile Function Wire Tests share: this controller's numbers, and starting it.

The setup, all on one host:

    Workstation (127.0.0.1, ephemeral UDP port) - the Peer: a Python operator workstation
        |  BACnet/IP, unicast both ways
    BACnetExampleBAAC   UDP --port   Device 389004

The Peer plays the operator workstation on a real site (a B-OWS / B-AWS): it puts itself
on Notification Class 1's Recipient_List, receives the controller's alarms, acknowledges
them, asks GetEventInformation, synchronises the controller's clock and sends it
DeviceCommunicationControl. It also writes Analog Value 1 the way any device allowed to
modify it would (L.4.2 Data Sharing: "modification of some or all of its BACnet objects by
another BACnet device"). Nothing reaches into the example any other way.
"""
import argparse
import sys
import time
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPOSITORY = TESTS.parent
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(TESTS))

import wiretest  # noqa: E402  (the vendored harness at the repository root)
import alarm_codec  # noqa: E402
from workstation import Workstation  # noqa: E402

# Match main.cpp.
DEVICE_INSTANCE = 389004
DEVICE = (wiretest.OBJECT_TYPE_DEVICE, DEVICE_INSTANCE)
OBJECT_TYPE_ANALOG_VALUE = 2
OBJECT_TYPE_CALENDAR = 6
OBJECT_TYPE_NOTIFICATION_CLASS = 15
OBJECT_TYPE_SCHEDULE = 17
DIAMOND = (OBJECT_TYPE_ANALOG_VALUE, 1)               # Analog Value 1, intrinsic OutOfRange [10, 90]
CRIMSON = (OBJECT_TYPE_NOTIFICATION_CLASS, 1)         # Notification Class 1
CHARTREUSE = (wiretest.OBJECT_TYPE_ANALOG_OUTPUT, 1)  # Analog Output 1, Saffron's target
SAFFRON = (OBJECT_TYPE_SCHEDULE, 1)                   # Schedule 1
CREAM = (OBJECT_TYPE_CALENDAR, 1)                     # Calendar 1, Date_List = December 25
NOTIFICATION_CLASS = 1
PRIORITY_TO_OFFNORMAL = 100
PRIORITY_TO_NORMAL = 200
SCHEDULE_WRITE_PRIORITY = 8
SCHEDULE_DEFAULT_VALUE = 20.0
SCHEDULE_WEEKLY_VALUE = 75.0          # Monday 08:00 onwards
SCHEDULE_EXCEPTION_VALUE = 5.0        # every date in Cream's Date_List
HIGH_VALUE = 95.0                     # above High_Limit 90
NORMAL_VALUE = 50.0
LOW_VALUE = 5.0                       # below Low_Limit 10
PROCESS_IDENTIFIER = 7                # the workstation's process, as its Recipient_List entry names it
NOTIFICATION_WAIT = 3.0               # seconds allowed for a notification to arrive
QUIET_WAIT = 2.0                      # seconds watched to show that nothing arrives


def parser(description):
    arguments = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    arguments.add_argument("--exe", default=str(wiretest.default_exe(REPOSITORY, "BACnetExampleBAAC")),
                           help="path to BACnetExampleBAAC (default: build/BACnetExampleBAAC)")
    arguments.add_argument("--port", type=int, default=47821, help="the controller's UDP port (default 47821)")
    return arguments


def start_controller(args, extra_arguments=()):
    return wiretest.start(args.exe, ["--port", args.port] + list(extra_arguments), "controller")


def describe(answer):
    return answer.describe()


def read(workstation, args, object_reference, property_identifier, array_index=None):
    """The decoded value of one property, or None (the Answer is printed on failure)."""
    answer = workstation.read_property(args.port, *object_reference, property_identifier, array_index)
    if not answer.ok:
        print(f"      read {object_reference} property {property_identifier}: {answer.describe()}")
    return answer.value


def write_diamond(workstation, args, value):
    return workstation.write_property(args.port, *DIAMOND, wiretest.PROPERTY_PRESENT_VALUE,
                                      wiretest.application_real(value))


def subscribe(workstation, args, confirmed=True, transitions=(True, True, True)):
    """Make the workstation Crimson's one recipient (AE-CRL-B: a WriteProperty of Recipient_List)."""
    return workstation.write_property(
        args.port, *CRIMSON, alarm_codec.PROPERTY_RECIPIENT_LIST,
        alarm_codec.destination(workstation.mac, PROCESS_IDENTIFIER, confirmed, transitions))


def get_event_information(workstation, args):
    """(summaries, more_events, Answer) from one GetEventInformation."""
    answer = workstation.request(lambda invoke_id: alarm_codec.get_event_information_request(invoke_id), args.port)
    if answer.frame is None or answer.frame.pdu_type != wiretest.PDU_COMPLEX_ACK:
        return None, None, answer
    summaries, more_events = alarm_codec.parse_event_summaries(answer.frame.payload)
    return summaries, more_events, answer


def summary_for(summaries, object_reference):
    for entry in summaries or []:
        if entry["object"] == object_reference:
            return entry
    return None


def describe_summary(entry):
    if entry is None:
        return "not listed"
    stamps = ", ".join(alarm_codec.date_time_text(stamp) for stamp in entry.get("time_stamps", []))
    return (f"{entry['object']} event-state={entry.get('event_state')} acked={entry.get('acked_transitions')} "
            f"time-stamps=[{stamps}]")


def acknowledge(workstation, args, event_state, time_stamp, source="Operator Olive"):
    """AcknowledgeAlarm for Diamond, the time of acknowledgment being now (host clock)."""
    now = time.localtime()
    time_of_acknowledgment = (bytes([now.tm_year - 1900, now.tm_mon, now.tm_mday, now.tm_wday + 1]),
                              bytes([now.tm_hour, now.tm_min, now.tm_sec, 0]))
    return workstation.request(lambda invoke_id: alarm_codec.acknowledge_alarm_request(
        invoke_id, PROCESS_IDENTIFIER, *DIAMOND, event_state, time_stamp, source, time_of_acknowledgment), args.port)


def from_diamond(notify_type, to_state=None):
    def matches(notification):
        return (notification.event_object == DIAMOND and notification.notify_type == notify_type and
                (to_state is None or notification.to_state == to_state))
    return matches


__all__ = ["Workstation", "alarm_codec", "wiretest"]
