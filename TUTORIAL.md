# Tutorial - extending and reviewing the B-AAC example

[README.md](README.md) says what this example *is*. This document is the *how*:
how to extend it into your own device, who serves which property, how to review
the result for conformance, and what goes wrong when you get it subtly right.

Read this once before you start changing `main.cpp`. The most expensive mistake
in this example is silent, and the section it lives in is
[Adding an object - read this first](#adding-an-object---read-this-first).

- [Extending the example](#extending-the-example)
- [Who serves what: the application or the stack?](#who-serves-what-the-application-or-the-stack)
- [Adding an object - read this first](#adding-an-object---read-this-first)
- [What each object type needs you to serve](#what-each-object-type-needs-you-to-serve)
- [Reviewing your device](#reviewing-your-device)
- [Troubleshooting](#troubleshooting)

## Extending the example

The example is intentionally small so it's easy to change.

**Change a sensor's value or name** - edit the constants / callbacks in
`main.cpp` (e.g. the initial value of `g_analogInput1Value`, or the `"Bronze"`
string in `GetPropertyCharString`).

**Change the device identity before you ship** - vendor ID, vendor name, model
name, description, firmware revision, DCC password, and device name are all in
the `CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of `main.cpp`, with a
per-field note on each saying what to change it to. That block is the
authoritative checklist; it is in the source rather than here so it cannot be
skipped by someone who only reads the code.

## Who serves what: the application or the stack?

The single most common question when reading `main.cpp` is "who answers this
property?" For the Analog Value **"Diamond"** - the alarm-capable object, and the
most interesting one in this example:

| Property | Served by | How |
|---|---|---|
| `Object_Identifier` | **stack** | generated from the object you added |
| `Object_Type` | **stack** | generated |
| `Object_List` | **stack** | generated (Device object) |
| `Property_List` | **stack** | generated |
| `Status_Flags` | **stack** | generated (and reflects the alarm state) |
| `Event_State` | **stack** | **computed** - because this example arms an intrinsic OutOfRange algorithm on Diamond (`SetIntrinsicOutOfRangeAlgorithm` + `SetAlarmsAndEventsForObjectEnabled`), the stack drives `Event_State` to `normal` / `high-limit` / `low-limit`. On an object with **no** alarming, nothing serves `Event_State` and it reads its datatype default `normal(0)` by coincidence - the opposite situation (see Bronze/Emerald/Hot Pink in [docs/PICS.md](docs/PICS.md)). |
| `Notification_Class` | **you** | `GetPropertyUnsignedInteger` - points at Crimson (NC 1) |
| `Present_Value` | **you** (writable) | `GetPropertyReal` / `SetPropertyReal` |
| `Object_Name` | **you** | `GetPropertyCharString` |
| `Units` | **you** | `GetPropertyEnumerated` |

That `Event_State` row is the whole point of B-AAC: arming the algorithm is what
turns a plain writable Analog Value into an alarm source, and it is why
`Event_State` moves from "defaulted by coincidence" to "genuinely computed."

Every object, not just this one, is in [docs/PICS.md](docs/PICS.md).

## Adding an object - read this first

Adding an object is the easiest place to ship a silent non-conformance. The
callbacks are **not uniformly strict**: `GetPropertyReal` / `GetPropertyEnumerated`
/ `GetPropertyUnsignedInteger` match on object type **and instance**, but a Get
callback returning `false` does **not** reliably produce an error. The stack errors
only for a short list (`Present_Value`, `Number_Of_States`, `Relinquish_Default`,
`Local_Date`, `Local_Time`, a Network Port's `APDU_Length`); for **everything
else** it **silently substitutes a default** - `Object_Name` -> the literal
`"undefined"`, `Units` -> `no-units(95)` - while `Property_List` still advertises
the property.

**Doesn't the `errorCode` out-parameter fix this?** Only if you use it, and only
where it is right to. Each `GetProperty*` callback ends with a `uint32_t*
errorCode` that the stack presets to `success` and reads only when you return
`false`, so you *can* turn any decline into a chosen BACnet error. But ending
every callback with `*errorCode = unknown-property` breaks the device: the
stack's decline-and-fabricate path is what answers required properties an
application is not expected to serve - the Device's `Max_APDU_Length_Accepted`,
`APDU_Timeout` and `Number_Of_APDU_Retries` among them. Name an error on the
catch-all and those start failing instead of answering. Set `errorCode` only
where *this device* knows the read is wrong; `main.cpp` does it in exactly one
place, `State_Text` with an out-of-range array index.

So a half-added object looks **healthy** on a scan and is non-conformant. When you
add an instance:

1. Add its instance constant (naming: a second object of a type is
   `"<Colour> 2"` - each object TYPE owns one colour series-wide).
2. `BACnetStack_AddObject` it in `main`, checking the return like every other
   stack call in this file.
3. Serve **every** required property in the relevant Get callbacks - for an
   Analog Value that is `Present_Value`, `Object_Name`, and `Units`.
4. If it should alarm, arm it (`SetAlarmsAndEventsForObjectEnabled` +
   `SetIntrinsicOutOfRangeAlgorithm`) and wire it to a Notification Class.
5. If it should be commandable (a Value type, unlike an Output type), enable
   `Priority_Array` and `Relinquish_Default` with `SetPropertyEnabled` and mark
   `Present_Value` writable - unlike an Output object, those are **not** on by
   default for a Value object, and `IsPropertyCommandable()` requires both
   enabled before it treats the object as commandable at all.
6. Read back **every** required property of the new object and **diff it against
   an existing one**. Anything reading `"undefined"`, `no-units`, or `0` where the
   existing object returns something real is a step you missed. Because the
   failure is silent (see above), this diff is the only thing that catches it.
   **"It scanned OK" is exactly the failure mode, not evidence against it.**

The block comment above the Get callbacks in `main.cpp` ("ADDING AN OBJECT? READ
THIS FIRST") is the in-code version of this.

## What each object type needs you to serve

The application must serve every REQUIRED property the stack does not generate.
It differs per type - this is the checklist, so you do not have to infer it:

| Object type | You must serve | Plus |
|---|---|---|
| Analog Input | `Present_Value` (Real), `Object_Name`, `Units` | - |
| Binary Input | `Present_Value` (Enumerated), `Object_Name` | `Polarity` |
| Multi-State Input | `Present_Value` (Unsigned), `Object_Name` | `Number_Of_States` |
| Analog Output (commandable) | `Object_Name`, `Units`, `Relinquish_Default` | `Present_Value`/`Priority_Array` resolved by the stack |
| Binary Output (commandable) | `Object_Name`, `Polarity`, `Relinquish_Default` | `Present_Value`/`Priority_Array` resolved by the stack |
| Multi-State Output (commandable) | `Object_Name`, `Number_Of_States`, `Relinquish_Default` | `Present_Value`/`Priority_Array` resolved by the stack |
| Analog Value (alarm-capable, commandable) | `Object_Name`, `Units` | `Present_Value` writable + intrinsic algorithm armed |
| Notification Class | `Object_Name` | `Priority`/`Ack_Required`/`Recipient_List` via `AddNotificationClassObject`/`AddRecipientToNotificationClass`, not a `GetProperty*` callback |
| Network Port | `Object_Name`, `Network_Type`, `Protocol_Level`, `Changes_Pending`, IP addressing | - |
| Schedule | `Object_Name`, `Reliability` | Weekly/exception data via `AddSchedule*`/`SetSchedule*`, not a `GetProperty*` callback |
| Calendar | `Object_Name`, `Present_Value` | `Date_List` cannot be populated - see [TODO.md](TODO.md) |

## Reviewing your device

After you have changed anything, review it against the conformance statement
rather than against "it looked fine in the explorer":

1. Regenerate [docs/PICS.md](docs/PICS.md) after editing `docs/objects.json`
   (see [Keeping the PICS honest](#keeping-the-pics-honest) below). A ⚠ row is a
   required property nothing serves.
2. Read **every** property listed for **every** object with a BACnet client, and
   compare the value against the PICS. `"undefined"`, `no-units` and `0` are the
   three shapes a missed callback takes.
3. Diff a new object of a type against the existing one of that type. Anything
   that differs and shouldn't is a callback that matched on instance.
4. Confirm the services you claim are actually gated correctly: a WriteProperty to
   a read-only input is rejected; a WriteProperty to Diamond or an output succeeds;
   AcknowledgeAlarm and GetEventInformation both respond.
5. Fire an alarm (WriteProperty Diamond above 90 or below 10) and confirm
   `Event_State` transitions and an EventNotification is observed, not just that
   the write succeeded.
6. Confirm a scheduled transition actually lands: press `s`, then re-read
   Chartreuse's `Present_Value` and `Priority_Array[8]` rather than trusting the
   console log alone.

### Keeping the PICS honest

`docs/PICS.md` is partly generated. `docs/objects.json` describes each object and
who serves which property; the series tool regenerates the object tables from it
plus the stack's own `docs/property-profile-reference.md` at the pinned commit:

```bash
python tools/gen-objects-properties.py BACnetProfileExample-B-AAC-CPP            # rewrite
python tools/gen-objects-properties.py BACnetProfileExample-B-AAC-CPP --check    # fail if stale
```

(That tool lives in the example-series repository, not in this one. If you only
have this repository, edit the generated block by hand and keep it matching the
callbacks in `main.cpp`.)

When you add an object or a property to `main.cpp`, update `docs/objects.json`
in the same change and regenerate. The `app` list is what the callbacks serve;
`accepted` is for a required property you deliberately leave to the stack's
default, and each one needs a justification. Anything required, not in `app` and
not in `accepted`, comes out as a ⚠ row - that is a defect, not a feature.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| On start-up the app prints a wall of red `Error:` lines but the device works | **Expected - this is not your bug.** Two benign sources, both from the stack's own debug logging: (1) the device receives its **own** broadcast I-Am and logs a decode cascade (*"Services is not supported service=[0]"* … *"Failed to process the incoming NPDU"*) - any BACnet/IP device that listens for broadcasts hears itself; (2) a one-time *"UUID has not been set. A UUID must be set for the BACnetSC device to start."* - the stack starts a BACnet/SC datalink these IP-only examples never configure. It appears once and does not spam. On a healthy start-up roughly half the output is these lines. |
| CMake error: *"CAS BACnet Stack adapter not found under: ..."* | Submodules not initialized. Run `git submodule update --init --recursive` (or pass `-D CAS_STACK_DIR=...`). |
| `CASBACnetStackDLL.h: No such file or directory` | Same - submodules not checked out. |
| Windows: *"No CMAKE_CXX_COMPILER could be found"* | Install Visual Studio with the "Desktop development with C++" workload, then re-run from a fresh terminal. |
| First build seems stuck for minutes | Normal - it's compiling ~600 stack files. Only the first build is slow. |
| App prints *"Failed to bind UDP port 47808"* | Another BACnet program is already using 47808. Stop it, or run with `--port <n>`. |
| Client sends Who-Is but sees no I-Am | Firewall is blocking UDP 47808, or the client and device are on different subnets (Who-Is is a broadcast). Allow the port; test on the same subnet first. |
| Replies show an unexpected device instance or vendor | Another BACnet device is already answering on this host/port. On Linux/macOS two processes can share the port and both reply; on Windows the example asks for `SO_EXCLUSIVEADDRUSE` (`common/SimpleUDP.cpp`) so this shows up as a bind failure instead. Stop the other device, or use `--port`. |
| A `Description` branch in `GetPropertyCharString` never seems to run | The stack checks `IsPropertyEnabled` **before** it ever reaches the callbacks. For an optional property (like the Device's `Description`) that check falls back to "is it required?", which is false - so an optional property needs an explicit `BACnetStack_SetPropertyEnabled` call, not just a callback branch. This example shipped exactly that bug once; it was caught by tracing the stack source, not by running it. |
| A commanded write to an Analog Value silently has no effect | Unlike an Output object, a Value object's `Priority_Array` and `Relinquish_Default` are **optional** and `IsPropertyCommandable()` requires both enabled before the write path is live - see step 5 of [Adding an object](#adding-an-object---read-this-first). |
| `ReinitializeDevice` SimpleACKs but the device never restarts, or the client times out waiting for the ACK | See [docs/deferred-restart-adoption.md](docs/deferred-restart-adoption.md) - the callback must accept-and-defer (`RequestRestart`), never restart in-line, or the ACK never reaches the wire before the process is gone. |
