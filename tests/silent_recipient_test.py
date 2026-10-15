#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-AAC Wire Test - Failure Mode: the operator workstation has gone silent.

    python3 tests/silent_recipient_test.py [--exe build/BACnetExampleBAAC] [--port 47821]

The workstation puts itself on Notification Class 1's Recipient_List for CONFIRMED
notifications and then stops answering - its SimpleACKs never come (a crashed or
unplugged front end). The controller is the client of a ConfirmedEventNotification, so
135-2024 cl. 5.4.4 applies: with no answer within APDU_Timeout it sends the request again
with the same invoke id, at most Number_Of_APDU_Retries times (12.11.29: "the maximum
number of times that an APDU shall be retransmitted"), then gives up.

  1. Device Number_Of_APDU_Retries reads 3 and APDU_Timeout 10000 ms.
  2. The alarm goes out, and nothing answers it.
  3. The same notification (same invoke id) arrives again, about APDU_Timeout apart -
     4 transmissions in all - and no 5th.
  4. The alarm itself is not lost: Event_State is HIGH_LIMIT and GetEventInformation
     still lists it, unacknowledged, for the operator to find when the front end returns.

This takes about 45 s: the controller's APDU_Timeout is 10 s (the 12.11.28 value for a
device that does not let it be modified).
"""
import sys
import time

import aac_setup as setup
from aac_setup import Workstation, alarm_codec, wiretest
from wiretest import record

PROPERTY_APDU_TIMEOUT = 11
PROPERTY_NUMBER_OF_APDU_RETRIES = 73
EXPECTED_RETRIES = 3
EXPECTED_APDU_TIMEOUT_MS = 10000


def run(workstation, args):
    retries = setup.read(workstation, args, setup.DEVICE, PROPERTY_NUMBER_OF_APDU_RETRIES)
    timeout_ms = setup.read(workstation, args, setup.DEVICE, PROPERTY_APDU_TIMEOUT)
    record("Number_Of_APDU_Retries reads 3, APDU_Timeout 10000 ms",
           (retries, timeout_ms) == (EXPECTED_RETRIES, EXPECTED_APDU_TIMEOUT_MS), f"read {retries}, {timeout_ms}")

    answer = setup.subscribe(workstation, args)
    record("The (soon silent) workstation is on the Recipient_List", answer.ok, answer.describe())
    answer = setup.write_diamond(workstation, args, setup.HIGH_VALUE)
    started = time.monotonic()
    record(f"Analog Value 1 <- {setup.HIGH_VALUE} is accepted", answer.ok, answer.describe())

    timeout = EXPECTED_APDU_TIMEOUT_MS / 1000.0
    expected = 1 + EXPECTED_RETRIES
    # Watch until one full timeout after the last expected retransmission has gone by.
    watch = expected * timeout + 3.0
    while time.monotonic() - started < watch:
        time.sleep(0.5)
    arrivals = [notification for notification in workstation.notifications
                if setup.from_diamond(alarm_codec.NOTIFY_TYPE_ALARM, alarm_codec.EVENT_STATE_HIGH_LIMIT)(notification)]
    record("The alarm arrived (confirmed) and was not answered", arrivals and arrivals[0].confirmed,
           f"{len(arrivals)} arrival(s)")
    if not arrivals:
        return
    invoke_ids = {notification.invoke_id for notification in arrivals}
    record(f"It was sent {expected} times in {watch:.0f} s - once plus {EXPECTED_RETRIES} retries - and then given up",
           len(arrivals) == expected, f"{len(arrivals)} transmission(s)")
    record("Every retransmission carries the same invoke id (cl. 5.4.4: the same request, again)",
           len(invoke_ids) == 1, f"invoke ids {sorted(invoke_ids)}")

    event_state = setup.read(workstation, args, setup.DIAMOND, alarm_codec.PROPERTY_EVENT_STATE)
    summaries, _, answer = setup.get_event_information(workstation, args)
    entry = setup.summary_for(summaries, setup.DIAMOND)
    record("The alarm is not lost: Event_State HIGH_LIMIT, still listed unacknowledged by GetEventInformation",
           event_state == alarm_codec.EVENT_STATE_HIGH_LIMIT and entry is not None and
           entry["acked_transitions"][alarm_codec.TO_OFFNORMAL] is False,
           f"read {event_state}, {setup.describe_summary(entry)}")


def main():
    args = setup.parser(__doc__).parse_args()
    controller = setup.start_controller(args)
    workstation = Workstation(answer_notifications=False)
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
