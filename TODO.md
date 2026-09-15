# TODO - B-AAC features not yet implemented

This example implements **as much of the B-AAC (Advanced Application Controller)
profile as the standard CAS BACnet Stack DLL supports today**. The items below are
the parts of B-AAC that are **not** implemented here, why, and what it would take.
They are revisited as the stack gains the capability.

See the README's "What this example does NOT do yet" section for the user-facing
summary; this file is the engineering detail.

## 1. Calendar 1 (Cream) Date_List is not evaluated

**Status: known stack limitation (cas-bacnet-stack issue #963).** Schedule 1
(Saffron)'s one-off exception event uses the inline calendar-date form of
`BACnetStack_AddScheduleExceptionEventWithCalendarEntry` rather than a reference to
Calendar 1 (Cream), because `BACnetStack_AddScheduleExceptionEventWithCalendarReference`
validates that the Calendar object exists but does **not** resolve its `Date_List` at
evaluation time - the stack has no read path for a Calendar object's `Date_List`
property (see that export's doc comment in `CASBACnetStackDLL.h`). There is also no
customer-facing export or callback to populate `Date_List` at all; the only generic
constructed-property callback (`RegisterCallbackGetPropertyConstructed`) is
test-tool-only and this example does not link the test-tool surface.

Cream is still added (`BACnetStack_AddObject`) so the object and its required
properties other than `Date_List` are correctly served; `Date_List` and Cream's
`Present_Value` (which would depend on it) are accepted with this note rather than
faked - `Present_Value` always answers `false`.

**To do when available:** once issue #963 adds a Date_List read/write path, switch
the exception to `AddScheduleExceptionEventWithCalendarReference` and evaluate
Cream's `Present_Value` for real.

## 2. Backup & Restore (DM-BR-B) on ReinitializeDevice

**Status: out of scope for B-AAC (noted for completeness).** B-AAC does not require
DM-BR-B, so this example accepts only `COLDSTART`/`WARMSTART` ReinitializeDevice
requests and does not register the backup/restore callbacks. (The stack logs a note
that the backup callbacks are unregistered - that is expected here.)

## 3. Fuller alarming coverage

This example demonstrates **one** intrinsic event algorithm (OutOfRange on an Analog
Value). The stack exposes ~19 `SetIntrinsic*Algorithm` functions (ChangeOfState,
ChangeOfValue, FloatingLimit, CommandFailure, BufferReady, ...). A richer B-AAC
could arm several object types. Left as a single, clear example on purpose.
