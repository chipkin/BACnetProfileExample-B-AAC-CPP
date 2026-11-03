# TODO - B-AAC: what is not yet done or not yet proven

This example performs the B-AAC Profile Function - alarms directed to a
recipient, acknowledgments tracked, a local schedule driven by a synchronised
clock - through the customer interface of the CAS BACnet Stack (`6.x` @
`1e7dffe2b`, example v1.5.1), and the Wire Tests in [`tests/`](tests/README.md) prove it against a
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
(vendored, shared by the whole series), or an override registered after
`RegisterCommonCallbacks()`. The Wire Tests take every time stamp from the
notification itself, so they do not depend on either clock.

## 2. Writing an empty Recipient_List

Filed: [#3959](https://github.com/chipkin/cas-bacnet-stack/issues/3959) (closed).

**Status: reported fixed in the stack; not re-checked in this example.** An
earlier stack answered a WriteProperty of Notification Class 1 `Recipient_List`
with an empty list (an opening and closing tag [3] with nothing between) with
Error `property` / `invalid-data-type`. The stack fix for #3959 (an empty list
clears the recipients, cl. 12.21.8) is in this pin, but no Wire Test writes an
empty list, so this example has not confirmed it. Writing a list that names a
recipient works (`alarm_test.py` section 8).

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
