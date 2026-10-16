#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-AAC Wire Test - the controller raises an alarm to an operator workstation and tracks its acknowledgment.

    python3 tests/alarm_test.py [--exe build/BACnetExampleBAAC] [--port 47821]

The Profile Function (135-2024 L.4.2, Alarm and Event Management): "Generation of limited
alarm and event notifications and the ability to direct them to recipients" and "Tracking
acknowledgments of alarms from human operators", with "configuration of event recipient
lists". The Peer is a Python operator workstation (wiretest.Workstation).

  1. AE-CRL-B: the workstation writes Notification Class 1's Recipient_List with itself
     as the one recipient (confirmed notifications, every transition). It reads back.
  2. AE-N-I-B: Analog Value 1 goes above its High_Limit (90) -> the workstation receives
     a ConfirmedEventNotification: to-state HIGH_LIMIT, out-of-range, alarm, ack required,
     priority 100. Event_State reads HIGH_LIMIT and Acked_Transitions shows to-offnormal
     unacknowledged.
  3. AE-INFO-B: GetEventInformation lists Analog Value 1 with that state and those bits.
  4. Failure Mode (cl. 13.5.2, 13.5.1.3.1): an AcknowledgeAlarm whose 'Time Stamp' is not
     the alarm's gets Error SERVICES / INVALID_TIMESTAMP, and nothing is acknowledged.
  5. AE-ACK-B: the acknowledgment with the notification's own time stamp gets a SimpleACK,
     Acked_Transitions to-offnormal becomes TRUE, and an ACK_NOTIFICATION reaches the
     workstation (13.5.2: "an event notification with a 'Notify Type' parameter equal to
     ACK_NOTIFICATION shall be issued").
  6. Back to normal -> a to-normal notification (ack required, priority 200).
  7. Failure Mode: nobody acknowledges the return to normal. Event_State is NORMAL but
     the to-normal transition stays unacknowledged, and GetEventInformation still lists
     the object for it.
  8. Control (AE-CRL-B again): the Recipient_List is rewritten to a second workstation.
     The next alarm (low-limit) reaches the second one and not the first - where an alarm
     goes is decided by that list, not by anything else in the test.
"""
import sys

import aac_setup as setup
from aac_setup import Workstation, alarm_codec, wiretest
from wiretest import record

ALARM = alarm_codec


def run(workstation, args):
    # --- 1. The workstation becomes the recipient ----------------------------------
    summaries, _, answer = setup.get_event_information(workstation, args)
    record("Control: GetEventInformation lists no event before any alarm", summaries == [],
           f"read {summaries}" if summaries is not None else answer.describe())
    answer = setup.subscribe(workstation, args)
    record("Recipient_List write (the workstation, confirmed, all transitions) is accepted", answer.ok,
           answer.describe())
    recipient_list = workstation.read_property(args.port, *setup.CRIMSON, ALARM.PROPERTY_RECIPIENT_LIST)
    record("Recipient_List reads back with the workstation's B/IP address",
           recipient_list.value_octets is not None and workstation.mac in recipient_list.value_octets,
           recipient_list.describe())

    # --- 2. The alarm ----------------------------------------------------------------
    mark = workstation.mark()
    answer = setup.write_diamond(workstation, args, setup.HIGH_VALUE)
    record(f"Analog Value 1 <- {setup.HIGH_VALUE} is accepted", answer.ok, answer.describe())
    alarm = workstation.wait_for_notification(
        setup.from_diamond(ALARM.NOTIFY_TYPE_ALARM, ALARM.EVENT_STATE_HIGH_LIMIT), setup.NOTIFICATION_WAIT, mark)
    record("The workstation receives the alarm", alarm is not None and alarm.confirmed,
           alarm.describe() if alarm else f"nothing in {setup.NOTIFICATION_WAIT} s")
    if alarm is None:
        return
    record("  ... from Device 389004, process id 7, Notification Class 1",
           (alarm.initiating_device, alarm.process_identifier, alarm.notification_class) ==
           (setup.DEVICE, setup.PROCESS_IDENTIFIER, setup.NOTIFICATION_CLASS),
           f"{alarm.initiating_device}, {alarm.process_identifier}, {alarm.notification_class}")
    record("  ... out-of-range, normal -> high-limit, ack required, priority 100",
           (alarm.event_type, alarm.from_state, alarm.ack_required, alarm.priority) ==
           (ALARM.EVENT_TYPE_OUT_OF_RANGE, ALARM.EVENT_STATE_NORMAL, True, setup.PRIORITY_TO_OFFNORMAL),
           alarm.describe())
    record("  ... with a date-and-time time stamp", alarm.time_stamp is not None,
           ALARM.date_time_text(alarm.time_stamp))
    event_state = setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_EVENT_STATE)
    record("Event_State reads HIGH_LIMIT", event_state == ALARM.EVENT_STATE_HIGH_LIMIT, f"read {event_state}")
    acked = setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_ACKED_TRANSITIONS)
    record("Acked_Transitions: to-offnormal unacknowledged", acked == [False, True, True], f"read {acked}")

    # --- 3. GetEventInformation --------------------------------------------------------
    summaries, more_events, answer = setup.get_event_information(workstation, args)
    entry = setup.summary_for(summaries, setup.DIAMOND)
    record("GetEventInformation lists Analog Value 1: HIGH_LIMIT, to-offnormal unacknowledged",
           entry is not None and entry["event_state"] == ALARM.EVENT_STATE_HIGH_LIMIT and
           entry["acked_transitions"] == [False, True, True],
           setup.describe_summary(entry) if summaries is not None else answer.describe())
    record("  ... with the alarm's time stamp as its to-offnormal time stamp",
           entry is not None and entry["time_stamps"][ALARM.TO_OFFNORMAL] == alarm.time_stamp,
           ALARM.date_time_text(entry["time_stamps"][ALARM.TO_OFFNORMAL]) if entry else "no entry")

    # --- 4. Failure Mode: a stale acknowledgment ------------------------------------
    date_octets, time_octets = alarm.time_stamp
    stale = (date_octets, bytes([time_octets[0], time_octets[1], (time_octets[2] + 30) % 60, time_octets[3]]))
    answer = setup.acknowledge(workstation, args, ALARM.EVENT_STATE_HIGH_LIMIT, stale)
    record("Failure Mode: an acknowledgment with the wrong time stamp gets SERVICES / INVALID_TIMESTAMP",
           answer.error == (ALARM.ERROR_CLASS_SERVICES, ALARM.ERROR_CODE_INVALID_TIMESTAMP), answer.describe())
    acked = setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_ACKED_TRANSITIONS)
    record("  ... and to-offnormal stays unacknowledged", acked == [False, True, True], f"read {acked}")

    # --- 5. The operator acknowledges ----------------------------------------------
    mark = workstation.mark()
    answer = setup.acknowledge(workstation, args, ALARM.EVENT_STATE_HIGH_LIMIT, alarm.time_stamp)
    record("AcknowledgeAlarm with the alarm's own time stamp gets a SimpleACK", answer.ok, answer.describe())
    acked = setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_ACKED_TRANSITIONS)
    record("Acked_Transitions: to-offnormal now acknowledged", acked == [True, True, True], f"read {acked}")
    ack_notification = workstation.wait_for_notification(
        setup.from_diamond(ALARM.NOTIFY_TYPE_ACK_NOTIFICATION), setup.NOTIFICATION_WAIT, mark)
    record("The workstation receives the ACK_NOTIFICATION for HIGH_LIMIT",
           ack_notification is not None and ack_notification.to_state == ALARM.EVENT_STATE_HIGH_LIMIT,
           ack_notification.describe() if ack_notification else f"nothing in {setup.NOTIFICATION_WAIT} s")
    summaries, _, answer = setup.get_event_information(workstation, args)
    entry = setup.summary_for(summaries, setup.DIAMOND)
    record("GetEventInformation shows the acknowledgment (still listed: Event_State is not NORMAL)",
           entry is not None and entry["acked_transitions"] == [True, True, True], setup.describe_summary(entry))

    # --- 6. Back to normal --------------------------------------------------------------
    mark = workstation.mark()
    answer = setup.write_diamond(workstation, args, setup.NORMAL_VALUE)
    record(f"Analog Value 1 <- {setup.NORMAL_VALUE} is accepted", answer.ok, answer.describe())
    to_normal = workstation.wait_for_notification(
        setup.from_diamond(ALARM.NOTIFY_TYPE_ALARM, ALARM.EVENT_STATE_NORMAL), setup.NOTIFICATION_WAIT, mark)
    record("The workstation receives the return to normal (high-limit -> normal, ack required, priority 200)",
           to_normal is not None and (to_normal.from_state, to_normal.ack_required, to_normal.priority) ==
           (ALARM.EVENT_STATE_HIGH_LIMIT, True, setup.PRIORITY_TO_NORMAL),
           to_normal.describe() if to_normal else f"nothing in {setup.NOTIFICATION_WAIT} s")

    # --- 7. Failure Mode: nobody acknowledges ----------------------------------------
    event_state = setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_EVENT_STATE)
    acked = setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_ACKED_TRANSITIONS)
    record("Unacknowledged return: Event_State NORMAL, to-normal unacknowledged",
           (event_state, acked) == (ALARM.EVENT_STATE_NORMAL, [True, True, False]), f"read {event_state}, {acked}")
    summaries, _, answer = setup.get_event_information(workstation, args)
    entry = setup.summary_for(summaries, setup.DIAMOND)
    record("  ... and GetEventInformation still lists Analog Value 1 for it",
           entry is not None and entry["event_state"] == ALARM.EVENT_STATE_NORMAL and
           entry["acked_transitions"] == [True, True, False], setup.describe_summary(entry))

    # --- 8. Control: the Recipient_List decides who hears it ---------------------------
    second = Workstation()
    try:
        answer = setup.subscribe(second, args)
        record("Recipient_List rewritten to a second workstation", answer.ok, answer.describe())
        mark = workstation.mark()
        record(f"Analog Value 1 <- {setup.LOW_VALUE} is accepted",
               setup.write_diamond(workstation, args, setup.LOW_VALUE).ok)
        redirected = second.wait_for_notification(
            setup.from_diamond(ALARM.NOTIFY_TYPE_ALARM, ALARM.EVENT_STATE_LOW_LIMIT), setup.NOTIFICATION_WAIT)
        record("The second workstation receives the low-limit alarm", redirected is not None,
               redirected.describe() if redirected else f"nothing in {setup.NOTIFICATION_WAIT} s")
        silence = workstation.wait_for_notification(lambda notification: True, setup.QUIET_WAIT, mark)
        record("Control: the first workstation, no longer on the list, receives nothing", silence is None,
               silence.describe() if silence else f"nothing in {setup.QUIET_WAIT} s")
    finally:
        second.close()

def main():
    args = setup.parser(__doc__).parse_args()
    controller = setup.start_controller(args)
    workstation = Workstation()
    try:
        run(workstation, args)
    finally:
        workstation.close()
        controller.stop()
        if not all(wiretest.results.RESULTS):
            controller.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
