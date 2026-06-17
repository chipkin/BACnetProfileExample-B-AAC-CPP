# TODO - B-AAC features not yet implemented

This example implements **as much of the B-AAC (Advanced Application Controller)
profile as the standard CAS BACnet Stack DLL supports today**. The items below are
the parts of B-AAC that are **not** implemented here, why, and what it would take.
They are revisited as the stack gains the capability.

See the README's "What this example does NOT do yet" section for the user-facing
summary; this file is the engineering detail.

## 1. SCHED-I-B - internal scheduling (Schedule + Calendar objects)

**Status: not implemented.** B-AAC requires SCHED-I-B: the device runs a
`Weekly_Schedule` / `Exception_Schedule` against its local clock and writes the
scheduled values to target objects.

**Why:** the **standard** `CASBACnetStackDLL.h` (the API this example links) has no
Schedule *execution* engine - there is no `BACnetStack_AddScheduleObject` /
`AddCalendarObject` and no engine that evaluates a schedule against time. (That
engine exists in a different stack build, not the standard DLL.) We could
`BACnetStack_AddObject(OBJECT_TYPE_SCHEDULE, ...)` and serve its properties
read-only, but it would not actually *schedule* anything, which would be
misleading - so the example omits it rather than ship a non-functional object.

**To do when available:** add a Schedule object + a Calendar object, seed a
`Weekly_Schedule`, and let the engine drive a target (e.g. Analog Output 1's
Present_Value) at the scheduled times.

## 2. AE-CRL-B - writable Recipient_List

**Status: partial.** The Notification Class recipient list is **seeded at
start-up** (`BACnetStack_AddRecipientToNotificationClass`), which satisfies the
"a recipient list exists and is used" half of AE-CRL-B. What is **not** wired is
accepting a **WriteProperty to the Notification Class's `Recipient_List`** so a
management station can reconfigure recipients at run time (the constructed
`BACnetDestination` write path).

**To do:** register the Notification Class `Recipient_List` as writable and decode
the written `BACnetDestination` list in the set-property path.

## 3. EventNotification recipient by device-instance

**Status: worked around.** A Notification Class recipient can be named by **device
instance** (the device then resolves the address with Who-Is) or by **address**.
The standard stack's `SendEventNotification` only implements the **address** form -
seeding a device-instance recipient logs *"must specify a recipient address instead
of a device identifier"* and the notification is not sent.

**Worked around here by** seeding the recipient by **address** (defaulting to the
local subnet broadcast, with UNCONFIRMED notifications) so alarms actually go out.
A confirmed, device-instance-addressed recipient needs the stack to implement the
Who-Is-resolve path in `SendEventNotification`.

## 4. Backup & Restore (DM-BR-B) on ReinitializeDevice

**Status: out of scope for B-AAC (noted for completeness).** B-AAC does not require
DM-BR-B, so this example accepts only `COLDSTART`/`WARMSTART` ReinitializeDevice
requests and does not register the backup/restore callbacks. (The stack logs a note
that the backup callbacks are unregistered - that is expected here.)

## 5. Fuller alarming coverage

This example demonstrates **one** intrinsic event algorithm (OutOfRange on an Analog
Value). The stack exposes ~19 `SetIntrinsic*Algorithm` functions (ChangeOfState,
ChangeOfValue, FloatingLimit, CommandFailure, BufferReady, ...). A richer B-AAC
could arm several object types. Left as a single, clear example on purpose.
