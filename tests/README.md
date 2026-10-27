# B-AAC Wire Tests

Tests that drive the running advanced application controller over BACnet/IP from
outside it, with a Python-simulated Peer, and fail when the controller's Profile
Function is removed. They are written against the series' shared harness in
[`../wiretest/`](../wiretest/README.md) (vendored, like `common/`); everything
specific to this example is here. Python 3 standard library only - nothing to
`pip install`.

## Running

Build the example (README "Build"), then from the repository root:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBAAC
```

On Windows, `--exe build\Release\BACnetExampleBAAC.exe` (or wherever your build
put it). It ends with `ALL WIRE TESTS PASSED` (exit 0) or the scripts that failed.
`--port` (default 47829) is the UDP port the test starts the example on. The run
takes a little over a minute; `silent_recipient_test.py` is most of it. Each script
also runs on its own with the same arguments. CI (`.github/workflows/release.yml`)
runs them on Linux after the smoke test.

## The setup

```
Workstation (127.0.0.1, ephemeral UDP port)  - the Peer: a Python operator workstation
    |  BACnet/IP, unicast both ways
BACnetExampleBAAC            UDP --port   - Device 389004
```

The Peer is a Python-simulated operator workstation (`wiretest.Workstation`), never
another example's binary. It is a client (it writes, reads, acknowledges,
synchronises the clock) and an event recipient at once: a background thread keeps
every EventNotification and SimpleACKs the confirmed ones within the controller's
APDU_Timeout - or, for the silent-recipient test, does not.

The Profile Function (135-2024 L.4.2): "Generation of limited alarm and event
notifications and the ability to direct them to recipients", "Tracking
acknowledgments of alarms from human operators", "Ability to schedule actions in
the local device based on date and time", with "Supports configuration of event
recipient lists", "Ability to respond to communication control messages" and
"Ability to synchronize its internal clock upon request".

## The scripts

| Script | Checks | What it proves |
|---|---:|---|
| `discovery_test.py` | 19 | Every listed property of every object reads as a value (Who-Is, `Object_List`, each `Property_List`); Device `Database_Revision` reads 12, one per object added at start-up |
| `configuration_test.py` | 18 | The Device's identity is configurable at start-up (`--deviceID`, `--deviceName`; cl. 12.1.1.3, 12.1.1.4): with no options the defaults; with `--deviceID 389904 --deviceName "Chipkin Example B-AAC Unit 2"` Who-Is, ReadProperty `Object_Name`, the ready line and Who-Has by name all see the configured identity, and Device 389004 is gone; an empty or 256-byte name keeps the default with a warning, a 255-byte one is kept whole; `--help` lists `--port`, `--deviceID`, `--deviceName`, `--dcc-password` and `--xml`, and `--xml` prints each frame as XML |
| `alarm_test.py` | 26 | The alarm path end to end: `Recipient_List` write (AE-CRL-B); a confirmed out-of-range alarm reaches the workstation (AE-N-I-B); `Event_State`, `Acked_Transitions` and GetEventInformation agree (AE-INFO-B); a stale acknowledgment is refused with `invalid-timestamp`; the real one is SimpleACKed, sets the bit and sends an ACK_NOTIFICATION (AE-ACK-B); an unacknowledged return to normal stays listed; rewriting the list to a second workstation moves the next alarm there and not to the first |
| `silent_recipient_test.py` | 7 | Failure Mode: a recipient that never SimpleACKs gets the same notification (same invoke id) 1 + `Number_Of_APDU_Retries` (3) times, `APDU_Timeout` (10 s) apart, then no more; the alarm stays listed, unacknowledged |
| `dcc_test.py` | 10 | Failure Mode: DCC with a wrong or missing password and ReinitializeDevice with a wrong one get `security` / `password-failure`, and the controller keeps alarming; the right password's `disable-initiation` stops the next notification while the controller still answers; `enable` brings notifications back (DM-DCC-B) |
| `schedule_test.py` | 5 | TimeSynchronization sets `Local_Date`; on December 25 Calendar 1 is TRUE and Schedule 1 / Analog Output 1 read 5.0 (`Priority_Array[8]` 5.0); Monday 09:00 gives 75.0; 07:00 gives 20.0 (SCHED-I-B, DM-TS-B) |

Every check prints `[PASS]` / `[FAIL]` with what it read, so a failure says what
came back instead.

## Each check fails without its feature

Every behaviour above was removed from `main.cpp`, one at a time; the example was
rebuilt (Windows STATIC) and the script run. All 14 were caught (the first failure line is shown).

| Mutation of `main.cpp` | Script | Caught by |
|---|---|---|
| M1 OutOfRange algorithm armed with `enable` false | alarm | "The workstation receives the alarm - nothing in 3.0 s" |
| M2 `enableEventDetection` false | alarm | "The workstation receives the alarm - nothing in 3.0 s" |
| M3 `Recipient_List` not writable | alarm | "Recipient_List write ... is accepted - Error class=2 code=40" |
| M4 Notification Class: to-offnormal ack not required | alarm | "... ack required, priority 100 - ... ack-required=False" |
| M5 Notification Class: to-normal ack not required | alarm | "Unacknowledged return: ... read 0, [True, True, True]" |
| M6 `AcknowledgeAlarm` callback refuses | alarm | "AcknowledgeAlarm with the alarm's own time stamp gets a SimpleACK - Error class=5 code=29" |
| M7 `Number_Of_APDU_Retries` served as 0 | silent_recipient | "Number_Of_APDU_Retries reads 3 ... - read 0, 10000"; "It was sent 4 times ... - 1 transmission(s)" |
| M8 DCC password not checked | dcc | "DCC disable-initiation, wrong password -> SECURITY / PASSWORD_FAILURE - SimpleACK" |
| M9 ReinitializeDevice password not checked | dcc | "ReinitializeDevice, wrong password -> SECURITY / PASSWORD_FAILURE - SimpleACK" |
| M10 DCC callback not registered | dcc | "DCC disable-initiation with the right password -> SimpleACK - Error class=4 code=26" |
| M11 `SetSystemTime` does not move the clock | schedule | "TimeSynchronization 2026-12-25 10:00: Local_Date reads 2026-12-25 - read 2026-10-15" |
| M12 `Local_Date` / `Local_Time` ignore the device clock | schedule | "TimeSynchronization 2026-12-25 10:00: Local_Date reads 2026-12-25 - read 2026-10-15" |
| M13 Calendar 1 date December 26 | schedule | "On a Calendar date: Cream TRUE, Saffron 5.0 ... - read ... (False, 20.0, 20.0, 20.0)" |
| M14 Monday transition moved to Tuesday | schedule | "Monday 2026-10-19 09:00: ... 75.0 ... - read (False, 20.0, 20.0, 20.0)" |

Three behaviours are the **stack's**, not `main.cpp`'s, so no example mutation can
remove them: refusing a stale acknowledgment (`invalid-timestamp`), sending the
ACK_NOTIFICATION, and dropping notifications under `disable-initiation`. Each is
checked against a control in the same run - the right time stamp is accepted, the
wrong one is not; notifications arrive before DISABLE and after ENABLE, and not
between.

## Shared helpers

The alarm and device-management encoders (`wiretest.alarm`: AcknowledgeAlarm,
GetEventInformation and its ACK parser, DeviceCommunicationControl, TimeSynchronization,
BACnetDestination, BACnetTimeStamp, `EventNotification`) and the Peer
(`wiretest.Workstation`) come from the series harness, `wiretest/` 0.6.0. They started
here and were folded into it. `aac_setup.py` holds this example's numbers.
