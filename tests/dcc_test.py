#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-AAC Wire Test - DeviceCommunicationControl silences the controller's alarms, with a password.

    python3 tests/dcc_test.py [--exe build/BACnetExampleBAAC] [--port 47821]

135-2024 L.4.2: "Ability to respond to communication control messages" (DM-DCC-B). The
controller is started with --dcc-password olive. Cl. 16.1.2: with DISABLE_INITIATION
"the responding BACnet-user shall discontinue the initiation of messages" (except I-Am /
I-Have answers and audit notifications) until a valid DCC ENABLE; and "If the 'Password'
parameter is invalid or absent when a password is required ... an Error-PDU with 'Error
Class' = SECURITY and 'Error Code' = PASSWORD_FAILURE shall be issued."

  1. Failure Mode: DCC DISABLE_INITIATION with a wrong password, and with none ->
     SECURITY / PASSWORD_FAILURE each time; ReinitializeDevice with a wrong password ->
     the same. Control: the controller still initiates - an alarm reaches the workstation.
  2. DCC DISABLE_INITIATION with the right password -> SimpleACK. The next transition
     happens (Event_State NORMAL) but no notification is initiated; the controller still
     answers (the reads in this step).
  3. DCC ENABLE with the right password -> SimpleACK; the next transition notifies again.
"""
import sys

import aac_setup as setup
from aac_setup import Workstation, alarm_codec, wiretest
from wiretest import record

PASSWORD = "olive"
ALARM = alarm_codec
SECURITY_PASSWORD_FAILURE = (ALARM.ERROR_CLASS_SECURITY, ALARM.ERROR_CODE_PASSWORD_FAILURE)


def dcc(workstation, args, enable_disable, password):
    return workstation.request(lambda invoke_id: ALARM.device_communication_control_request(
        invoke_id, enable_disable, password), args.port)


def transition(workstation, args, value, to_state):
    """Write Analog Value 1 and return the matching notification (or None) and Event_State."""
    mark = workstation.mark()
    answer = setup.write_diamond(workstation, args, value)
    if not answer.ok:
        print(f"      write Analog Value 1 <- {value}: {answer.describe()}")
    notification = workstation.wait_for_notification(
        setup.from_diamond(ALARM.NOTIFY_TYPE_ALARM, to_state), setup.NOTIFICATION_WAIT, mark)
    return notification, setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_EVENT_STATE)


def run(workstation, args):
    record("The workstation is on the Recipient_List", setup.subscribe(workstation, args).ok)

    # --- 1. Failure Mode: the wrong password -------------------------------------------
    answer = dcc(workstation, args, ALARM.DCC_DISABLE_INITIATION, "wrong")
    record("Failure Mode: DCC disable-initiation, wrong password -> SECURITY / PASSWORD_FAILURE",
           answer.error == SECURITY_PASSWORD_FAILURE, answer.describe())
    answer = dcc(workstation, args, ALARM.DCC_DISABLE_INITIATION, None)
    record("Failure Mode: DCC disable-initiation, no password -> SECURITY / PASSWORD_FAILURE",
           answer.error == SECURITY_PASSWORD_FAILURE, answer.describe())
    answer = workstation.request(lambda invoke_id: wiretest.reinitialize_device_request(
        invoke_id, wiretest.REINITIALIZE_WARMSTART, "wrong"), args.port)
    record("Failure Mode: ReinitializeDevice, wrong password -> SECURITY / PASSWORD_FAILURE",
           answer.error == SECURITY_PASSWORD_FAILURE, answer.describe())
    notification, event_state = transition(workstation, args, setup.HIGH_VALUE, ALARM.EVENT_STATE_HIGH_LIMIT)
    record("Control: the refused DCC changed nothing - the high-limit alarm reaches the workstation",
           notification is not None, notification.describe() if notification else
           f"nothing in {setup.NOTIFICATION_WAIT} s (Event_State {event_state})")

    # --- 2. Disable initiation -----------------------------------------------------------
    answer = dcc(workstation, args, ALARM.DCC_DISABLE_INITIATION, PASSWORD)
    record("DCC disable-initiation with the right password -> SimpleACK", answer.ok, answer.describe())
    mark = workstation.mark()
    answer = setup.write_diamond(workstation, args, setup.NORMAL_VALUE)
    record("While disabled the controller still answers: Analog Value 1 <- 50.0 SimpleACKed", answer.ok,
           answer.describe())
    silence = workstation.wait_for_notification(lambda notification: True, setup.QUIET_WAIT, mark)
    event_state = setup.read(workstation, args, setup.DIAMOND, ALARM.PROPERTY_EVENT_STATE)
    record("The return to normal happens (Event_State NORMAL) but no notification is initiated",
           event_state == ALARM.EVENT_STATE_NORMAL and silence is None,
           f"read {event_state}; " + (silence.describe() if silence else f"nothing in {setup.QUIET_WAIT} s"))

    # --- 3. Enable -------------------------------------------------------------------------
    answer = dcc(workstation, args, ALARM.DCC_ENABLE, PASSWORD)
    record("DCC enable with the right password -> SimpleACK", answer.ok, answer.describe())
    notification, event_state = transition(workstation, args, setup.LOW_VALUE, ALARM.EVENT_STATE_LOW_LIMIT)
    record("Enabled again: the low-limit alarm reaches the workstation", notification is not None,
           notification.describe() if notification else
           f"nothing in {setup.NOTIFICATION_WAIT} s (Event_State {event_state})")


def main():
    args = setup.parser(__doc__).parse_args()
    controller = setup.start_controller(args, ["--dcc-password", PASSWORD])
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
