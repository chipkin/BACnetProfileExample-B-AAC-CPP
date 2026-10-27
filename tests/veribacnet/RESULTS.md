# VeriBACnet results

The latest VeriBACnet run of this folder's project, summarised by hand from
that run's `report.json`. The run's own Results Folder (reports, packet
captures, wire logs) is not published: it holds the testing machine's network
addresses.

| | |
|---|---|
| Date | 2026-10-27 |
| Example | BACnet B-AAC (Advanced Application Controller) Example - C++ v1.5.0, CAS BACnet Stack 6.x @ 69b6249f |
| Profile | B-AAC (BACnet Advanced Application Controller) |
| Transport | BACnet/IP, UDP port 47829 |
| VeriBACnet | 0.20.0 (its test device uses CAS BACnet Stack 6.0.23.0) |
| Test plan | 227 BTL tests (ANSI/ASHRAE 135.1-2023) selected for the B-AAC profile |
| Password | The example was started with a DeviceCommunicationControl / ReinitializeDevice password (`--dcc-password`, a test value), and the project gives VeriBACnet the same password |
| Result | **94 PASS · 2 FAIL · 0 ERROR · 131 SKIP** |

**Judged BTL-clean on BACnet/IP**: no failure or error is the example's own
fault, both failures are tracked, and every skipped test has a stated
reason. See "What BTL-clean means" in [README.md](README.md). This is not BTL
certification.

**Measured coverage:** 96 of the 227 selected tests ran (94 passed, 2
failed). Of the 131 skipped:
- 52 wait on the test tool or a test-script fix;
- 24 need an operator;
- 54 do not apply to this device or need something it does not have;
- 1 needs a restart of the device in the middle of the test.

Event notification, alarm acknowledgement, configurable recipient lists and the
DeviceCommunicationControl tests that show the device's notifications being
silenced and resumed now have tests that ran and passed. Two requirements
still had no test that ran at all: scheduling (none of the 39 Schedule tests
can run yet) and the device's own Who-Is with a range. So this verdict is
still starred (BTL-clean\*) until the test tool can run them. This example's
own Wire Tests cover those functions.

**What changed since the previous run (2026-10-25, 214 tests).**
- No example code changed. The test tool now writes to the device itself to
  put Analog Value 1 into and out of alarm, to add itself to Notification
  Class 1's recipient list and to set the starting state of the
  DeviceCommunicationControl tests, so many tests that waited for an operator
  now run.
- New tests that passed: AcknowledgeAlarm (9.1.1.1), Out of Range High Limit
  and Low Limit (8.4.6 and the automated 8.4.6, 8.4.7, 8.5.6 and 8.5.7
  forms), Recipient_List supports Device Identifier recipients (7.3.2.21.3.5),
  and the DeviceCommunicationControl disable-initiation tests 9.24.1.8,
  9.24.1.9 and 9.24.1.10 (the device stays silent while disabled and resumes
  afterwards).
- Also passing now: the Write Support Test Procedure (7.2.2) and Writing a
  Single Property to Multiple Objects (9.23.1.3, the previous run's one
  failure).
- The event-list test (9.8.1) now skips: the AcknowledgeAlarm test above
  leaves Analog Value 1's return-to-normal notification unacknowledged, and
  the test needs a device with no active event state. The device is right.
- 13 tests were added by the new test plan: the automated 8.4.7 and 8.5.7
  forms and the 9.24.1.2 requirement (which does not apply at this Protocol
  Revision).

## The tests that did not pass

| Test | Result | Why |
|---|---|---|
| 8.5.6 Out of Range High Limit Transition (unconfirmed) | FAIL | The device sent the correct return-to-normal notification, but 65 ms before it answered the test tool's write. The test tool keeps an unexpected message for only 50 ms, so it had already dropped it when the test began to wait. Three isolated re-runs passed. A test-tool defect, tracked. |
| 7.3.2.21.3.4 Recipient_List transitions (confirmed) | FAIL | The same cause: the notification arrived 85 ms before the write's answer, and the test tool had acknowledged it but then forgot it. Three isolated re-runs passed. Tracked with the one above. |

### Skipped tests

| Tests | Why |
|---|---|
| 9.1.1.2-9.1.1.6, 9.1.1.14 (AcknowledgeAlarm), 9.8.1 | The previous test (9.1.1.1) leaves Analog Value 1's return-to-normal notification unacknowledged, and these tests need none outstanding. A test-script defect, tracked. |
| 9.1.1.8-9.1.1.11, 9.1.1.15, 9.1.2.x, 7.3.1.11.1 (AcknowledgeAlarm, 12) | Need per-test values the project cannot give yet. Not measured. |
| 9.24.1.7, 9.24.1.12 (DeviceCommunicationControl) | Need an operator to confirm a restart. |
| 8.34.2 Who-Is Request with a Device Instance Range | Needs an operator to make the device send a Who-Is with a range. |
| 9.27.1.2, 9.27.1.4, 9.27.2.3, 9.27.2.4 (ReinitializeDevice with a password) | The device answered correctly; the operator's confirmation of the restart was not available in an unattended run. |
| 7.2.8, 7.3.1.13.1, 7.3.1.13.2, 7.3.1.19.1-7.3.1.19.3, 7.3.1.20.1, 7.3.1.20.2, 7.3.1.22.1, 7.3.1.22.2, 8.4.17.10, 8.5.17.10 | Need an operator; the run was unattended. |
| 7.3.2.10.8, 7.3.2.10.9, 7.3.2.10.10, 9.32.1.12, 9.32.1.13 | Need an operator to restart the device with a new name, instance or UTC offset. |
| 9.8.3 GetEventInformation (automated) | Asks the operator to drive an Integer Value object this device does not have. A test-script defect, tracked. |
| 7.3.2.23.x and their Revision 4 forms (Schedule, 27) | Need the test tool to write and restore a Schedule configuration. That is not built yet for this device, whose Weekly_Schedule is not writable. Not measured. |
| 7.3.2.21.3.1, .2, .6 (Notification Class recipients) | The scripts accept only an Event Enrollment as the alarm source, or need a scenario the project cannot describe. This device has no Event Enrollment: Analog Value 1 alarms on its own. A test-script defect, tracked. |
| 7.3.2.21.3.7 Recipient_List non-volatility | Needs the device to be restarted during the test. |
| 9.23.2.20, 9.23.2.22 | Need a writable time or date-range property; this device has none, and the test tool cannot yet encode a date range. |
| 7.3.2.8.1-7.3.2.8.3 (Calendar) | Calendar 1's date list is kept by the stack and is not writable, so the test tool cannot set the entry each test needs. |
| 7.3.2.23.3.2-7.3.2.23.3.7, 9.24.1.2, 9.24.1.3, 9.24.1.4, 9.24.1.5, 9.24.2.3 | Apply only to devices at an older Protocol_Revision (before Revision 4 schedules, or before DISABLE was deprecated). |
| 7.2.4, 7.2.10, 7.2.11, 7.3.1.10.1 | Need a writable date, date-range or Event_Enable property; this device has none. |
| 8.4.6 / 8.4.7 / 8.5.6 / 8.5.7 automated forms for Analog Input, Analog Output, Integer, Positive Integer and Large Analog Values (20) | This device has no alarm on those objects, or no such object. |
| 7.3.2.10.3-7.3.2.10.6 (Database_Revision) | Do not apply: this device creates and deletes no objects, and changes an object's name or identifier only by a restart. |
| 7.3.1.12 Notify_Type | Needs one event-generating object reporting as an alarm and another reporting as an event; this device has one. |
| 9.8.2-9.8.5 | Need Event Enrollment objects; this device has none. |
| 9.8.6 GetEventInformation chaining | The device cannot be given enough active alarms to split its answer, and the standard skips the test then. |
| 9.22.2.4, 9.23.2.7 | No writable value has a restricted range; the standard skips the test then. |
| 9.22.2.10, 9.23.2.13, 9.22.2.11, 9.23.2.18 | Need a writable fixed-size array, or a property tied to optional functionality; this device has neither. |

Five B-AAC requirements had no runnable VeriBACnet test script, so they were
not run:
- 7.3.1.11.3 and 7.3.1.11.4 (Acked_Transitions variants);
- 7.3.2.23.15 Write_Every_Scheduled_Action FALSE Test;
- the ConfirmedEventNotification and UnconfirmedEventNotification initiation
  requirements (8.4, 8.5). The 8.4.6 and 8.5.6 tests are selected and ran
  (above); the test tool still lists the requirement as missing.

No public issue has been opened for any of these.
