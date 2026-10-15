# TODO - B-AAC: what is not yet done or not yet proven

This example implements the B-AAC (Advanced Application Controller) profile's
capabilities through the customer interface of the CAS BACnet Stack (`6.x` @
`64b2cfac5`). The items below are what it does not do yet, or does without an
automated proof, and what it would take. Re-check them whenever the Stack Pin
moves.

See the README's "What this example does NOT do yet" section for the user-facing
summary; this file is the engineering detail.

## 1. Wire Tests for the Profile Function

**Status: own scope.** The only automated test is discovery
(`tests/discovery_test.py`: every listed property of every object reads). The
alarm, acknowledgement, recipient-list, schedule and time-sync behaviour was
checked by hand on the wire at this pin (CHANGELOG 1.3.0), not by a test that
fails when the feature is removed. Wire Tests to add, each run against a Python
peer:

- set Crimson's `Recipient_List` to the peer; write Diamond to 95 and assert a
  to-offnormal EventNotification arrives; write 50 and assert to-normal;
- GetEventInformation shows the event state and `Acked_Transitions`;
  AcknowledgeAlarm with the received time stamp is SimpleACKed and reflected;
- TimeSynchronization to 2026-12-25 makes Calendar 1 `Present_Value` TRUE and
  Chartreuse 5.0; to a Monday 09:00 makes Chartreuse 75.0;
- `--dcc-password`: a wrong password gets `security` / `password-failure` on
  DeviceCommunicationControl and ReinitializeDevice.

## 2. AcknowledgeAlarm does not check the event state or time stamp

**Status: own scope.** The callback accepts an acknowledgement for Analog Value 1
(Diamond) and refuses one for any other object (VALUE_OUT_OF_RANGE). It does not
compare the acknowledged event state or time stamp with the alarm it
acknowledges, so a stale acknowledgement is accepted. Whether the stack tracks
`Acked_Transitions` itself has not been checked.

## 3. Backup & Restore (DM-BR-B) on ReinitializeDevice

**Status: out of scope for B-AAC (noted for completeness).** B-AAC does not require
DM-BR-B, so this example accepts only `COLDSTART`/`WARMSTART` ReinitializeDevice
requests and does not register the backup/restore callbacks. (The stack logs a note
that the backup callbacks are unregistered - that is expected here.)

## 4. Fuller alarming coverage

This example demonstrates **one** intrinsic event algorithm (OutOfRange on an Analog
Value). The stack exposes ~19 `SetIntrinsic*Algorithm` functions (ChangeOfState,
ChangeOfValue, FloatingLimit, CommandFailure, BufferReady, ...). A richer B-AAC
could arm several object types. Left as a single, clear example on purpose.

## 5. Stack documentation gap - filed as [#3958](https://github.com/chipkin/cas-bacnet-stack/issues/3958)

**The Schedule and Calendar engines read the Device's `Local_Date` / `Local_Time`,
and the customer header does not say so.** `BACnetDBDevice::RunSchedule` and
`GetLocalDateParts` (stack `source/BACnetDBDevice.cpp` at `64b2cfac5`) evaluate
against those two Device properties, which the stack does not default
(`docs/property-profile-reference.md`: "No default - a read fails with
`value-not-initialized`"). The doc comments of `BACnetStack_AddScheduleObject`
and `BACnetStack_AddCalendarObject` in `CASBACnetStackDLL.h` do not mention that
the application must serve them with `CallbackGetPropertyDate` /
`CallbackGetPropertyTime`. Up to 1.2.2 this example did not, so Schedule 1 never
evaluated - its `Present_Value` read `property` / `value-not-initialized` and
Chartreuse was never written - with no diagnostic. Evidence: the discovery Wire
Test at 1.2.2 + this pin failed on Device 56, Device 57 and Schedule 1 property
85, all Error class 2 code 72; with the two callbacks it passes 18/18.

