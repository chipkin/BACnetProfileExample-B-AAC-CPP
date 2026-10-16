# TODO - B-AAC: what is not yet done or not yet proven

This example performs the B-AAC Profile Function - alarms directed to a
recipient, acknowledgments tracked, a local schedule driven by a synchronised
clock - through the customer interface of the CAS BACnet Stack (`6.x` @
`64b2cfac5`), and the Wire Tests in [`tests/`](tests/README.md) prove it against a
Python operator workstation. The items below are what it does not do, or what
the stack does differently from what one might expect. Re-check them whenever
the Stack Pin moves.

None of them is a `[KNOWN GAP]` in the Wire Tests: each is either own scope (not
done) or behaviour the tests do not depend on.

## 1. Event time stamps are on the host clock, not the device clock

**Status: own scope, needs `common/`.** TimeSynchronization moves the device
clock that `Local_Date` / `Local_Time` report (`g_clockOffsetSeconds`,
`main.cpp`), so the Schedule and Calendar follow it. Event notification time
stamps come from `CallbackGetSystemTime`, which `common/CASExampleHelper.cpp`
registers and which returns the host clock. After a sync the two disagree. The
fix is to register a `GetSystemTime` that adds the offset - a `common/` change
(frozen for this round), or an override registered after
`RegisterCommonCallbacks()`. The Wire Tests take every time stamp from the
notification itself, so they do not depend on either clock.

## 2. Writing an empty Recipient_List is refused

Filed: [#3959](https://github.com/chipkin/cas-bacnet-stack/issues/3959).

**Status: stack behaviour, observed; not confirmed as a defect.** WriteProperty of
Notification Class 1 `Recipient_List` with an empty list (an opening and closing
tag [3] with nothing between) is answered Error `property` /
`invalid-data-type` (class 2, code 9). The stack's log says
`BACnetBusinessLogic::SetProperty() ... Invalid datatype=[255]` - it takes the
datatype from the first element and there is none. Writing a list that names a
recipient works, so a workstation can still redirect alarms (`alarm_test.py`
section 8 does). 135-2024 has no sentence found that says an empty BACnetLIST
must be writable; the coordinator decides whether to file it.

## 3. Alarms raised during DCC disable-initiation are not sent later

**Status: as the standard allows.** 135-2024 16.1.2 says the device "shall
discontinue the initiation of messages" until a valid ENABLE. The stack drops the
notification of a transition that happens meanwhile; the transition itself is
kept (`Event_State`, `Acked_Transitions`, GetEventInformation). `dcc_test.py`
checks the silence and that the next transition after ENABLE is sent, not a
replay.

## 4. Backup & Restore (DM-BR-B) on ReinitializeDevice

**Status: out of scope for B-AAC.** B-AAC does not require DM-BR-B, so this
example accepts only `COLDSTART`/`WARMSTART` ReinitializeDevice requests and does
not register the backup/restore callbacks. (The stack logs a note that the
backup callbacks are unregistered - that is expected here.)

## 5. Fuller alarming coverage

This example demonstrates **one** intrinsic event algorithm (OutOfRange on an
Analog Value). The stack exposes ~19 `SetIntrinsic*Algorithm` functions
(ChangeOfState, ChangeOfValue, FloatingLimit, CommandFailure, BufferReady, ...).
A richer B-AAC could arm several object types. Left as a single, clear example
on purpose.

## 6. Stack documentation gap - filed as [#3958](https://github.com/chipkin/cas-bacnet-stack/issues/3958)

**The Schedule and Calendar engines read the Device's `Local_Date` /
`Local_Time`, and the customer header does not say so.** `BACnetDBDevice::RunSchedule`
and `GetLocalDateParts` (stack `source/BACnetDBDevice.cpp` at `64b2cfac5`)
evaluate against those two Device properties, which the stack does not default
(`docs/property-profile-reference.md`: "No default - a read fails with
`value-not-initialized`"). The doc comments of `BACnetStack_AddScheduleObject`
and `BACnetStack_AddCalendarObject` in `CASBACnetStackDLL.h` do not mention that
the application must serve them with `CallbackGetPropertyDate` /
`CallbackGetPropertyTime`. Up to 1.2.2 this example did not, so Schedule 1 never
evaluated - its `Present_Value` read `property` / `value-not-initialized` and
Chartreuse was never written - with no diagnostic. Evidence: the discovery Wire
Test at 1.2.2 + this pin failed on Device 56, Device 57 and Schedule 1 property
85, all Error class 2 code 72; with the two callbacks it passes 18/18.

## 7. Number_Of_APDU_Retries defaults to 0 in the stack

Filed as a documentation gap: [#3960](https://github.com/chipkin/cas-bacnet-stack/issues/3960) (0 is conformant; cl. 12.11.29 suggests 3).

**Status: worked around here; stack default, noted for the series.** The stack's
`CAS_BACNET_DEVICE_DEFAULT_NUMBER_OF_APDU_RETRIES` is 0 (`BACnetDBDevice.h` at
`64b2cfac5`), and the stack reads the value through the application's
`GetPropertyUnsignedInteger` when it retries a confirmed request. An example that
does not serve it never retransmits a ConfirmedEventNotification (seen on the
wire at 1.3.0: one transmission, no retry in 12 s). 135-2024 12.11.29 allows 0
("If this device does not perform retries, then this property shall be set to
zero") and suggests 3. This example serves 3 (`silent_recipient_test.py`).
Every other example in the series that sends confirmed notifications or
requests has the same default.
