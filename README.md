# BACnet B-AAC (Advanced Application Controller) - C++ example

A tutorial example showing how to implement **as much of the BACnet B-AAC
(Advanced Application Controller)** device profile as the
[CAS BACnet Stack](https://store.chipkin.com/services/stacks/bacnet-stack)
supports today, in C++. It answers **ReadProperty / ReadPropertyMultiple**,
accepts **WriteProperty / WritePropertyMultiple**, generates **intrinsic
alarms** (EventNotifications when a value goes out of range), accepts
**AcknowledgeAlarm** and **GetEventInformation**, accepts a WriteProperty that
redirects its alarm recipient list, runs an internal **Schedule** that writes a
target object on a weekly basis and on the dates in a **Calendar**, sets its
device clock from **TimeSynchronization**, and handles
**DeviceCommunicationControl** and **ReinitializeDevice**.

What a B-AAC is for, in one sentence from ANSI/ASHRAE 135-2024 Annex L.4.2:
**"Generation of limited alarm and event notifications and the ability to direct
them to recipients"**, **"Tracking acknowledgments of alarms from human
operators"** and the **"Ability to schedule actions in the local device based on
date and time"**. This example does all three against a Peer - an operator
workstation - and the [Wire Tests](#wire-tests) prove it; see
[The scenario](#the-scenario-an-alarm-reaches-the-operator-and-is-acknowledged).

**[Download a prebuilt binary](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP/releases)**
(Windows and Linux x64) - or build it yourself, see [Build](#build) below.

- **[TUTORIAL.md](TUTORIAL.md)** - how to extend this example and how to review
  it for conformance. Read it when you start turning this into your own device.
- **[docs/PICS.md](docs/PICS.md)** - the Protocol Implementation Conformance
  Statement: every object, every property, and who answers it.

> **Versions:** this document describes **example v1.4.0**, built and verified
> against **CAS BACnet Stack 6.0.23** (`6.x` @ `64b2cfac5`), at
> **Protocol_Revision 30**, with the vendored `common/` helper at **v3.3.0**.
> Running the example prints all three - if what it prints disagrees with this
> line, trust the program and check `CHANGELOG.md`.

> **What is proven, and how.** Everything in [The scenario](#the-scenario-an-alarm-reaches-the-operator-and-is-acknowledged)
> below is driven over BACnet/IP by the automated [Wire Tests](#wire-tests),
> against a Python operator workstation, through the customer interface of the
> stack at this pin; each check fails when the feature it checks is removed from
> `main.cpp`. What is not proven is in "What this example does NOT do yet" and
> [TODO.md](TODO.md).

## The scenario: an alarm reaches the operator, and is acknowledged

The Peer is an **operator workstation** (a B-OWS / B-AWS on a real site; in the
Wire Tests, a few dozen lines of Python in [`tests/workstation.py`](tests/workstation.py)).

1. **The workstation subscribes (AE-CRL-B).** It writes Notification Class 1
   "Crimson"'s `Recipient_List` with itself as the recipient, for **confirmed**
   notifications on every transition.
2. **The process goes out of range (AE-N-I-B).** Analog Value 1 "Diamond" is
   written to 95 - above its `High_Limit` of 90. The stack's intrinsic
   OutOfRange algorithm moves `Event_State` to `high-limit` and the workstation
   receives a **ConfirmedEventNotification**: to-state `high-limit`, event type
   out-of-range, notify type alarm, **ack required**, priority 100.
3. **The operator looks (AE-INFO-B).** GetEventInformation lists Diamond:
   `high-limit`, with its to-offnormal transition unacknowledged.
4. **The operator acknowledges (AE-ACK-B).** AcknowledgeAlarm, quoting the
   notification's own time stamp, gets a SimpleACK; `Acked_Transitions` shows
   to-offnormal acknowledged and an **ACK_NOTIFICATION** goes to the recipients
   (135-2024 13.5.2).
5. **Back to normal.** Diamond = 50 sends a to-normal notification, which also
   needs acknowledging.
6. **The schedule follows the clock (SCHED-I-B, DM-TS-B).** The workstation
   time-syncs the controller to December 25: Calendar 1 "Cream" turns TRUE and
   Schedule 1 "Saffron" drives Analog Output 1 "Chartreuse" to 5.0. A Monday at
   09:00 gives 75.0; 07:00 gives Schedule_Default 20.0.
7. **Communication control (DM-DCC-B).** DeviceCommunicationControl
   `disable-initiation` (with the `--dcc-password`) stops the controller sending
   alarms while it still answers; `enable` resumes them.

**Failure Modes**, each demonstrated by a Wire Test:

- **A stale acknowledgment** - AcknowledgeAlarm with a time stamp that is not the
  alarm's is refused with `services` / `invalid-timestamp` and acknowledges
  nothing (13.5.2, 13.5.1.3.1). The stack performs this check.
- **Nobody acknowledges** - the return to normal stays unacknowledged:
  `Event_State` is `normal`, the to-normal bit of `Acked_Transitions` is FALSE,
  and GetEventInformation keeps listing Diamond until someone does.
- **The workstation goes silent** - its SimpleACKs never come. The controller
  sends the same ConfirmedEventNotification again every `APDU_Timeout` (10 s),
  `Number_Of_APDU_Retries` (3) times, then gives up; the alarm is not lost - it
  is still listed, unacknowledged, by GetEventInformation.
- **The wrong DCC password** - DeviceCommunicationControl and ReinitializeDevice
  with a wrong or missing password get `security` / `password-failure`, and the
  controller keeps sending alarms.

### What is Simulation

**Simulation** - non-BACnet scaffolding standing in for the physical world - is
small here, and outside the BACnet Surface:

- **The sensor values.** Analog Input 1 "Bronze" is moved by the up/down arrow
  keys; the other inputs are constants. A real controller reads hardware.
- **The device clock.** `Local_Date` / `Local_Time` are the host's clock plus an
  offset that TimeSynchronization sets. A real controller sets its real-time
  clock.

Diamond's out-of-range value is **not** simulated: it is written over BACnet by
another device (in the tests, the workstation), which L.4.2 Data Sharing
provides for ("modification of some or all of its BACnet objects by another
BACnet device"). The alarm, the acknowledgment tracking, the recipient list, the
schedule, the calendar and communication control are the stack's real engines.

## What this example supports

| Requirement | BIBB | This example |
|---|---|:--:|
| ReadProperty | DS-RP-B | ✅ |
| ReadPropertyMultiple | DS-RPM-B | ✅ |
| WriteProperty | DS-WP-B | ✅ |
| WritePropertyMultiple | DS-WPM-B | ✅ |
| Generate event notifications | AE-N-I-B | ✅ (intrinsic OutOfRange) |
| Accept AcknowledgeAlarm | AE-ACK-B | ✅ |
| Answer GetEventInformation | AE-INFO-B | ✅ |
| Configurable recipient list | AE-CRL-B | ✅ |
| Internal scheduling | SCHED-I-B | ✅ |
| DeviceCommunicationControl | DM-DCC-B | ✅ |
| ReinitializeDevice | DM-RD-B | ✅ (cold/warm start) |
| Time synchronisation | DM-TS-B / DM-UTC-B | ✅ (sets the device clock: `Local_Date` / `Local_Time`, which the Schedule and Calendar follow) |
| Who-Is/I-Am (answer + initiate), Who-Has/I-Have | DM-DDB-A,B, DM-DOB-B | ✅ |

### Services (executed / B-side)

| Service | Notes |
|---------|-------|
| ReadProperty / ReadPropertyMultiple | Responds to property reads, single or batched (DS-RP-B / DS-RPM-B). |
| WriteProperty / WritePropertyMultiple | Accepts writes to the commandable outputs and Diamond/Crimson (DS-WP-B / DS-WPM-B). |
| Who-Is / I-Am | Answers Who-Is with I-Am, and broadcasts an I-Am on start-up and after a restart (DM-DDB-B). Also initiates a Who-Is on start-up (DM-DDB-A). |
| Who-Has / I-Have | Answers Who-Has with I-Have (DM-DOB-B). |
| DeviceCommunicationControl | Enables/disables initiation, password-checked (DM-DCC-B). |
| ReinitializeDevice | Accepts COLDSTART/WARMSTART, password-checked, deferred restart (DM-RD-B). |
| TimeSynchronization / UTCTimeSynchronization | Sets the device clock from a management station's time sync (DM-TS-B / DM-UTC-B); see [The device clock](#the-device-clock-dm-ts-b--dm-utc-b). |
| (Un)ConfirmedEventNotification | Sent when Diamond's intrinsic algorithm transitions (AE-N-I-B). |
| AcknowledgeAlarm | Accepts an acknowledgement for an active event (AE-ACK-B). |
| GetEventInformation | Reports active events (AE-INFO-B). |

## Intrinsic alarming (the headline B-AAC capability)

An **intrinsic** alarm is generated by the object itself, from an algorithm the
stack runs, with no external Event Enrollment. This example arms **Analog Value 1
"Diamond"** with an **OutOfRange** algorithm: while its `Present_Value` stays in
`[10, 90]` the object is `NORMAL`; cross a limit and it transitions to
`high-limit` / `low-limit` (off-normal). On each transition the stack sends an
**EventNotification** to the recipients of **Notification Class 1 "Crimson"**.

Try it: `WriteProperty` Diamond's `Present_Value` to `95` - the device prints the
write, `Event_State` becomes `high-limit`, and an EventNotification goes out to
the recipients. Write it back to `50` and it returns to `NORMAL` (a second
notification). Until a workstation writes the `Recipient_List`, the one recipient
is the **local subnet broadcast** with **unconfirmed** notifications (so any client
sees the alarm); point it at a specific client in `main.cpp`, or write the list.

**Confirmed notifications are retried.** A recipient that asks for confirmed
notifications must SimpleACK each one. If it does not, the controller sends it
again after `APDU_Timeout` (10 s, the stack's value), up to
`Number_Of_APDU_Retries` times. `main.cpp` serves that property as **3** (the
135-2024 12.11.29 suggested default); left unserved it reads 0, which means "this
device does not perform retries" - one lost datagram and the operator never sees
the alarm.

**Acknowledgment is checked by the stack.** For an AcknowledgeAlarm the stack
runs the 13.5.2 procedure: it refuses a `Time Stamp` that is not the latest one
for the acknowledged transition (`invalid-timestamp`), sets the
`Acked_Transitions` bit, answers SimpleACK and sends an ACK_NOTIFICATION to the
same recipients. `main.cpp`'s `AcknowledgeAlarm` callback runs before that check;
it can refuse an operator (`service-request-denied`), and here it logs who
acknowledged.

**Redirecting the recipient list (AE-CRL-B).** Notification Class 1 "Crimson"'s
`Recipient_List` is seeded at start-up **and** registered writable
(`BACnetStack_SetPropertyWritable`), so a management station can also
`WriteProperty` a new recipient list at run time - the stack decodes and stores
the `BACnetDestination` list itself; nothing in `main.cpp` needs to. A
device-instance recipient (rather than an address) is resolved automatically: the
stack's Device-Address-Binding cache chases it with Who-Is and starts delivering
once it resolves (cas-bacnet-stack issue #1328).

## Scheduling (SCHED-I-B)

**Schedule 1 "Saffron"** writes **Analog Output 1 "Chartreuse"**'s `Present_Value`
at priority 8, on two kinds of trigger:

- A **weekly** transition (`Weekly_Schedule`): every Monday at 08:00, Chartreuse
  moves to the demo value.
- An **exception** (`Exception_Schedule`) that **references Calendar 1
  "Cream"**, added with `BACnetStack_AddScheduleExceptionEventWithCalendarReference`:
  on every date in Cream's `Date_List`, Chartreuse goes to 5.0 for the whole day.
  Cream is **stack-held** (`BACnetStack_AddCalendarObject`): the stack keeps its
  `Date_List` - one entry, December 25 of every year
  (`BACnetStack_AddCalendarDateEntry`) - and derives its `Present_Value` (TRUE on
  a listed date). Change the holidays by changing the Calendar, not the
  Schedule.

Outside any active weekly or exception entry, `Schedule_Default` applies (20.0,
Chartreuse's steady-state setpoint). The stack's schedule engine evaluates
against the **Device's `Local_Date` and `Local_Time`** on every tick - the device
clock below - so a TimeSynchronization to a Monday after 08:00 moves Chartreuse to
75.0, and one to December 25 moves it to 5.0. Pressing **`s`** at the console
adds a `Weekly_Schedule` entry for **right now** on the device clock, so the new
entry is immediately the latest transition today and Chartreuse moves within a
second or two.

## The device clock (DM-TS-B / DM-UTC-B)

The Device's `Local_Date` and `Local_Time` are served by `main.cpp`
(`GetPropertyDate` / `GetPropertyTime`): the host's wall clock plus the
correction the last TimeSynchronization or UTCTimeSynchronization applied
(`SetSystemTime`). The stack does not invent these two properties, and its
Schedule and Calendar engines read them - an example that does not serve them has
a Schedule that never evaluates. A real device would set its real-time clock
instead of keeping an offset. Event time stamps and COV lifetimes use the shared
helper's `GetSystemTime`, which stays on the host clock.

`Priority_For_Writing` (8) sits below a manual override: `WriteProperty`
Chartreuse at a priority 1-7 and it wins over the schedule until that slot is
relinquished.

## The device this example creates

```
Device 389004  "Chipkin Example B-AAC"   (Vendor 389 - Chipkin Automation Systems)
    ├── Analog Input  1       "Bronze"      read-only sensor (REAL, deg C)
    ├── Binary Input  1       "Emerald"     read-only sensor (active/inactive)
    ├── Multi-State Input 1   "Hot Pink"    read-only sensor (state 1..3)
    ├── Analog Output 1       "Chartreuse"  writable, commandable (REAL)
    ├── Binary Output 1       "Fuchsia"     writable, commandable (0/1)
    ├── Multi-State Output 1  "Indigo"      writable, commandable (state 1..3)
    ├── Analog Value 1        "Diamond"     writable; intrinsic OutOfRange ALARM
    ├── Notification Class 1  "Crimson"        routes Diamond's alarms to recipients; Recipient_List writable (AE-CRL-B)
    ├── Network Port 1        "Vermilion"   the BACnet/IP port (required)
    ├── Schedule 1             "Saffron"     SCHED-I-B: drives Chartreuse on a weekly schedule + the dates in Cream
    └── Calendar 1             "Cream"       stack-held Date_List: December 25, every year
```

The three inputs are the series' shared minimum; the outputs come from B-SA/B-ASC;
**Diamond + Crimson are the B-AAC alarming additions; Saffron + Cream are the B-AAC
scheduling additions**. Object names follow the series' colour convention (Device
is always "Chipkin Example B-AAC").

Every required property of every object, and who answers it, is in
[docs/PICS.md](docs/PICS.md).

## What this example does NOT do yet

Full detail and "what it would take" is in **[TODO.md](TODO.md)**.

- **Event time stamps are on the host clock, not the synchronised device
  clock.** A TimeSynchronization moves `Local_Date` / `Local_Time` (and so the
  Schedule and Calendar), but alarm time stamps come from the shared helper's
  `GetSystemTime`, which stays on the host clock. A real device has one clock.
- **An alarm raised while initiation is disabled is not sent later.** During
  DCC `disable-initiation` a transition still happens (`Event_State`,
  `Acked_Transitions`, GetEventInformation all show it) but its notification is
  dropped, not queued; 135-2024 16.1.2 asks only that initiation stop.
- **An empty `Recipient_List` cannot be written.** WriteProperty of an empty list
  is answered `property` / `invalid-data-type` by the stack at this pin; write a
  list naming a recipient instead. See TODO.md.
- **One alarm source.** Only Analog Value 1 has event reporting.

## Requires the CAS BACnet Stack (licensed product)

This example **builds against the CAS BACnet Stack, which is a commercial Chipkin
product** - it is not free or open source, and there is no public/trial build.
The stack is referenced here as the **private** git submodule
`submodules/cas-bacnet-stack`; you can only fetch and build it once you have a CAS
BACnet Stack license and access to that repository.

**To get the CAS BACnet Stack (and access to build this example), contact
Chipkin:** <https://store.chipkin.com/services/stacks/bacnet-stack> or
sales@chipkin.com.

You do not need a stack licence to *read* this example, or to run a
[prebuilt release binary](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP/releases).
The licence is what lets you *build* it - that is the part the stack submodule
gates.

## What's in this repository

This is a **self-contained** project. It ships:

- `main.cpp` - the example device.
- `common/` - the shared helper (UDP, callbacks, CLI, keyboard) vendored in.
- `CMakeLists.txt` - the build, the same on Windows, Linux, and macOS.
- `docs/PICS.md` - the conformance statement.
- `TODO.md` - what B-AAC requires that this example does not yet do, and why.
- `tests/` - the Wire Tests (see [Wire Tests](#wire-tests)), and `wiretest/`, the
  series' shared Python harness they are written against (vendored, like `common/`).
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack as a git submodule**
  (private; requires a license - see above). Its sources are compiled into the
  executable, so there is no library or DLL to build, ship, or install.

## Prerequisites

- A C++17 compiler (MSVC, GCC, or Clang).
- CMake >= 3.15.
- Git (to fetch the stack submodule).

### Windows

- **C++ compiler** - install
  [Visual Studio Community](https://visualstudio.microsoft.com/downloads/)
  (free) and select the **"Desktop development with C++"** workload.
- **CMake** - from <https://cmake.org/download/>, or `winget install Kitware.CMake`.

### Linux / macOS

- Debian/Ubuntu: `sudo apt install build-essential cmake git`
- macOS: `xcode-select --install` and `brew install cmake`

## Build

CMake only, and the same two commands on every platform:

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP.git
cd BACnetProfileExample-B-AAC-CPP

cmake -B build -S .
cmake --build build --config Release
```

Already cloned without `--recursive`? Run `git submodule update --init --recursive`
first - the build needs the stack submodule.

> **The first build takes a few minutes** - it compiles the entire CAS BACnet
> Stack (~600 source files) into the executable. Rebuilds after that are
> incremental and take seconds.

If your CAS BACnet Stack lives somewhere other than the bundled submodule, point
CMake at it: `cmake -B build -S . -D CAS_STACK_DIR=/path/to/cas-bacnet-stack`.

## Run

```bash
# Linux / macOS
./build/BACnetExampleBAAC

# Windows
.\build\Release\BACnetExampleBAAC.exe
```

Expected output:

```
BACnet B-AAC (Advanced Application Controller) Example - C++ v1.4.0
CAS BACnet Stack version: 6.0.23.0
Common helper (common/) version: 3.3.0
FYI: Listening for BACnet/IP on UDP port 47808 (Network Port 1).
TX 21 bytes to 192.168.3.255:47808 (broadcast) (Network Port 1) - Unconfirmed: I-Am
TX 8 bytes to 192.168.3.255:47808 (broadcast) (Network Port 1) - Unconfirmed: Who-Is
FYI: Device 389004 ("Chipkin Example B-AAC") ready. Vendor ID 389. Press 'h' for help.
WriteProperty: Analog Output 1 (Chartreuse) <- 20.00 @ priority 8
```

The two `TX` lines are the start-up unsolicited I-Am and the start-up Who-Is
(DM-DDB-A - this example also discovers other devices on the subnet). Both go to
the **local subnet broadcast** address (here `192.168.3.255`, computed from the
Network Port's interface), not the global `255.255.255.255`. As clients talk to
the device you'll see `RX ... bytes from ...` and `TX ... bytes to ...` lines
showing the traffic. The `WriteProperty` line is Schedule 1 (Saffron)'s first
evaluation writing `Schedule_Default` to Chartreuse.

The device listens on UDP **47808** (BACnet/IP). Allow that port through your
firewall. To use a different port, pass `--port` (see below).

> **A wall of red `Error:` lines at start-up is expected and is not your bug** -
> it is the stack's own debug logging (the device hearing its own broadcast I-Am,
> and a one-time BACnet/SC UUID notice). [TUTORIAL.md](TUTORIAL.md#troubleshooting)
> explains both.

### Command-line options

| Option | Default | Meaning |
|--------|---------|---------|
| `--port <n>` | `47808` | UDP port to listen on (BACnet/IP). |
| `--deviceID <n>` | `389004` | The device's BACnet instance number (BACnet requires this to be configurable). |
| `--dcc-password <string>` | none | Require this password on DeviceCommunicationControl and ReinitializeDevice. Prints a `FYI: ... require a password` line at start-up (never the password). |
| `--help`, `-h` | - | Show usage and exit. |
| `--version` | - | Print the example, stack, and `common/` helper versions, then exit. |

### Interactive commands

While the example runs, these keys are available:

| Key | Action |
|-----|--------|
| `h` | Show the version information and this command list. |
| `q` | Quit. |
| up arrow | Increase Analog Input 1 (`Bronze`) by 1.1. |
| down arrow | Decrease Analog Input 1 (`Bronze`) by 1.1. |
| `s` | Advance Schedule 1 (`Saffron`) with a `Weekly_Schedule` transition for right now (see [Scheduling](#scheduling-sched-i-b)). |

## Verify

With the [CAS BACnet Explorer](https://store.chipkin.com/products/tools/cas-bacnet-explorer)
(or any client):

1. **Discover** - Who-Is -> I-Am from `389004` (vendor `389`).
2. **Object model** - twelve objects incl. Analog Value "Diamond", Notification
   Class "Crimson", Schedule "Saffron" and Calendar "Cream". `Object_List` lists
   them all; `Protocol_Revision` = 30.
3. **ReadPropertyMultiple** - read several properties of "Diamond" in one request
   (DS-RPM-B).
4. **Fire an alarm** - WriteProperty Diamond `Present_Value` = `95`; read
   `Event_State` (`high-limit`) and watch the EventNotification arrive. Write `50`
   to return to `NORMAL`.
5. **Acknowledge** - send AcknowledgeAlarm for Diamond (AE-ACK-B) with the
   notification's time stamp; the device logs who acknowledged it. Query active
   events with GetEventInformation (AE-INFO-B).
6. **Redirect the recipient list (AE-CRL-B)** - WriteProperty Notification Class 1
   (Crimson) `Recipient_List` with a new destination; fire another alarm and confirm
   it goes to the new recipient instead of the seeded one.
7. **Scheduling (SCHED-I-B)** - read Schedule 1 (Saffron)'s `Weekly_Schedule`,
   `Effective_Period` and `Schedule_Default`, and Calendar 1 (Cream)'s
   `Date_List` (December 25, any year) and `Present_Value`; press `s` at the
   console and confirm Analog Output 1 (Chartreuse) `Present_Value` changes to
   75.0 and `Priority_Array[8]` shows the write.
8. **Time sync (DM-TS-B)** - send TimeSynchronization for 2026-12-25 10:00: the
   Device's `Local_Date` / `Local_Time` read it back, Cream's `Present_Value`
   is TRUE and Saffron's (and Chartreuse's) is 5.0. Sync to a Monday at 09:00 and
   it is 75.0; to 07:00 the same day and it is back to 20.0.
9. **Device management** - DeviceCommunicationControl `disable-initiation` /
   `enable`; ReinitializeDevice `WARMSTART` - each is accepted. Start the example
   with `--dcc-password s3cret` and a request without it is refused with
   `password-failure`.

For a property-by-property review against the conformance statement, see
[TUTORIAL.md](TUTORIAL.md).

## Wire Tests

Steps 1-9 above, automated, plus the Failure Modes: Python plays the operator
workstation and drives the running example over BACnet/IP from outside it. Python 3
standard library only:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBAAC          # Linux/macOS
python tests\run_wire_tests.py --exe build\Release\BACnetExampleBAAC.exe   # Windows
```

| Script | What it proves |
|---|---|
| `discovery_test.py` | Every listed property of every object reads as a value |
| `alarm_test.py` | Recipient_List write; the alarm reaches the workstation; GetEventInformation; a stale acknowledgment refused; the real one accepted, with its ACK_NOTIFICATION; an unacknowledged return to normal stays listed; the list decides who hears it |
| `silent_recipient_test.py` | A silent recipient gets the notification 1 + 3 times, then the controller gives up and keeps the alarm (about 45 s) |
| `dcc_test.py` | Wrong / missing password refused; `disable-initiation` stops alarms while the device answers; `enable` resumes them |
| `schedule_test.py` | TimeSynchronization moves Local_Date; Calendar and Schedule follow it to 5.0 / 75.0 / 20.0 |

It ends with `ALL WIRE TESTS PASSED` (exit 0), in a little over a minute. CI runs
it on Linux after the smoke test. [tests/README.md](tests/README.md) says what each
check proves and how each was shown to fail without its feature.

## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
There is one example repository per standardized device profile in ASHRAE 135-2024 Annex L. An example marked ⛔ is blocked: the stack cannot yet perform that profile's function through its customer interface, and the example's README says what it does today. Pick the profile your device claims, then the language you build in. "Ask" means the example hasn't been built yet for that language - [contact Chipkin](https://store.chipkin.com/contact-us) if you need one.

### Controllers (Annex L.4)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-SS** Smart Sensor | [B-SS-CPP](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) | [B-SS-Node](https://github.com/chipkin/BACnetProfileExample-B-SS-Node) | [B-SS-CS](https://github.com/chipkin/BACnetProfileExample-B-SS-CS) | [B-SS-Rust](https://github.com/chipkin/BACnetProfileExample-B-SS-Rust) | [B-SS-Python](https://github.com/chipkin/BACnetProfileExample-B-SS-Python) | [B-SS-Go](https://github.com/chipkin/BACnetProfileExample-B-SS-Go) |
| **B-SA** Smart Actuator | [B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ASC** Application Specific Controller | [B-ASC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP) | [B-ASC-Node](https://github.com/chipkin/BACnetProfileExample-B-ASC-Node) | Ask | Ask | Ask | Ask |
| **B-AAC** Advanced Application Controller | [B-AAC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-BC** Building Controller | [B-BC-CPP](https://github.com/chipkin/BACnetProfileExample-B-BC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Life safety controllers (Annex L.5)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LSC** Life Safety Controller | [B-LSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) 🚧 | Ask | Ask | Ask | Ask | Ask |
| **B-ALSC** Advanced Life Safety Controller | [B-ALSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Access control controllers (Annex L.6)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) ⛔ blocked on [stack #2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150), [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) | Ask | Ask | Ask | Ask | Ask |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Lighting controllers (Annex L.11)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LD** Lighting Device | [B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-LS** Lighting Supervisor | [B-LS-CPP](https://github.com/chipkin/BACnetProfileExample-B-LS-CPP) | Ask | Ask | Ask | Ask | Ask |

### Elevator controllers (Annex L.13)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-EM** Elevator Monitor | [B-EM-CPP](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-EC** Elevator Controller | [B-EC-CPP](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-AEC** Advanced Elevator Controller | [B-AEC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AEC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Authentication and authorization (Annex L.14)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) ⛔ blocked on [stack #2043](https://github.com/chipkin/cas-bacnet-stack/issues/2043) | Ask | Ask | Ask | Ask | Ask |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) ⛔ blocked on [stack #3934](https://github.com/chipkin/cas-bacnet-stack/issues/3934) | Ask | Ask | Ask | Ask | Ask |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) ⛔ blocked on [stack #2032](https://github.com/chipkin/cas-bacnet-stack/issues/2032) | Ask | Ask | Ask | Ask | Ask |
| **B-SCHUB** BACnet/SC Hub | [B-SCHUB-CPP](https://github.com/chipkin/BACnetProfileExample-B-SCHUB-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GENERAL** General device (Annex L.8) | *(satisfied by every example above)* | — | — | — | — | — |

### Operator interfaces and workstations (Annex L.1–L.3, L.9–L.10, L.12)

Client-side profiles.

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-OD** Operator Display | [B-OD-CPP](https://github.com/chipkin/BACnetProfileExample-B-OD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-OWS** Operator Workstation | planned | — | — | — | — | — |
| **B-AWS** Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-XAWS** Extended Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-LSAP** Life Safety Annunciator Panel | planned | — | — | — | — | — |
| **B-LSWS** Life Safety Workstation | planned | — | — | — | — | — |
| **B-ALSWS** Advanced Life Safety Workstation | planned | — | — | — | — | — |
| **B-ACSD** Access Control Security Display | planned | — | — | — | — | — |
| **B-ACWS** Access Control Workstation | planned | — | — | — | — | — |
| **B-AACWS** Advanced Access Control Workstation | planned | — | — | — | — | — |
| **B-LOD** Lighting Operator Display | planned | — | — | — | — | — |
| **B-ALWS** Advanced Lighting Workstation | planned | — | — | — | — | — |
| **B-LCS** Lighting Control Station | planned | — | — | — | — | — |
| **B-ALCS** Advanced Lighting Control Station | planned | — | — | — | — | — |
| **B-ED** Elevator Display | planned | — | — | — | — | — |
| **B-EWS** Elevator Workstation | planned | — | — | — | — | — |
| **B-AEWS** Advanced Elevator Workstation | planned | — | — | — | — | — |

🚧 = in progress. ⛔ = Blocked Example (blocked on the named stack gap). "Ask" = not yet built for that language; contact Chipkin if you need it. Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
<!-- PROFILE-TABLE:END -->

## References

- **ANSI/ASHRAE 135** - object model (Clause 12), alarming/events (Clause 13),
  services (Clause 16), device profiles (Annex L).
- **What is BACnet?** - Chipkin's introduction:
  <https://docs.chipkin.com/protocols/bacnet/>.
- **CAS BACnet Stack** - product page and documentation:
  <https://store.chipkin.com/services/stacks/bacnet-stack>.
- **CAS BACnet Explorer** - client for testing this device:
  <https://store.chipkin.com/products/tools/cas-bacnet-explorer>.
- **Shared helper used by this example** - [`common/README.md`](common/README.md).

See also [TUTORIAL.md](TUTORIAL.md), [docs/PICS.md](docs/PICS.md),
[TODO.md](TODO.md), [CHANGELOG.md](CHANGELOG.md), and [AGENTS.md](AGENTS.md).
