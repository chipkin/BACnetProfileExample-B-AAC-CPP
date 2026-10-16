# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - unreleased

Profile-functional: the example now performs the B-AAC Profile Function against a
Peer and the Wire Tests prove it (series glossary, `docs/GLOSSARY.md`).

### Added

- Wire Tests use the shared `wiretest/` 0.6.0: `tests/alarm_codec.py` and `tests/workstation.py` are folded into it as `wiretest.alarm` and `wiretest.Workstation`.
- **Wire Tests for the Profile Function**, against a Python operator workstation
  (`tests/workstation.py`) that is both a client and an event recipient:
  `alarm_test.py` (26 checks: `Recipient_List` write, a confirmed alarm at the
  workstation, `Event_State` / `Acked_Transitions` / GetEventInformation, a stale
  acknowledgment refused with `invalid-timestamp`, the real one SimpleACKed with
  its ACK_NOTIFICATION, an unacknowledged return to normal still listed, alarms
  redirected to a second workstation), `silent_recipient_test.py` (7),
  `dcc_test.py` (10) and `schedule_test.py` (5) - phase 1's hand checks of time
  sync, Calendar and `--dcc-password`, automated. Each check was shown to fail
  with its feature removed from `main.cpp` (`tests/README.md`). Generic helpers
  for the series harness: `tests/alarm_codec.py`, `tests/workstation.py`.
- README "The scenario" (Profile Function quoted from 135-2024 L.4.2, the Peer,
  the Failure Modes) and "What is Simulation".

### Fixed

- **A confirmed alarm to a silent recipient was sent once and never again.** The
  stack reads Device `Number_Of_APDU_Retries` (73) through the application's
  callback when it retries a confirmed request, and its default is 0 ("this
  device does not perform retries", 12.11.29). `main.cpp` now serves 3, the
  clause's suggested default: a recipient that does not SimpleACK gets the
  notification again every `APDU_Timeout` (10 s), three times. PICS row regenerated.
- **`AcknowledgeAlarm` callback and docs described the wrong check.** The stack
  runs the 13.5.2 procedure itself - unknown object, no alarm configured, the
  time stamp (`invalid-timestamp`), the event state - and the callback runs
  before the time-stamp check, so its "acknowledged" log line printed even for an
  acknowledgment the stack then refused. Its object check was unreachable (the
  stack answers `no-alarm-configured` first) and used the wrong error code. The
  callback now logs who is acknowledging and that the stack decides; README /
  TODO.md no longer say a stale acknowledgment is accepted (the Wire Test shows it
  is refused).

### Changed

- TODO.md rewritten: the Wire Test and acknowledgment items are done; added the
  event time stamps on the host clock, the refused empty `Recipient_List` write,
  notifications dropped (not queued) under `disable-initiation`, and the stack's
  `Number_Of_APDU_Retries` default of 0.
- `release.yml` Wire Test step renamed for the five scripts. APP_VERSION 1.3.0 ->
  1.4.0.

## [1.3.0] - unreleased

### Fixed

- **Schedule 1 (Saffron) never evaluated.** The stack's Schedule and Calendar
  engines evaluate against the Device's `Local_Date` (56) and `Local_Time` (57),
  which the stack does not default; this example did not serve them, so both
  read Error `property` / `value-not-initialized`, Saffron's `Present_Value` did
  too, and Chartreuse was never written by the schedule (the README's "press
  `s` and Chartreuse moves" did not happen). Found by the new discovery Wire
  Test (17/18 before: Device 56, Device 57, Schedule 1 property 85, each Error
  class 2 code 72). `main.cpp` now serves both from `GetPropertyDate` /
  `GetPropertyTime`. The customer header does not document the dependency -
  recorded in `TODO.md` item 5 as a stack documentation gap (not filed).
- **"Synchronises its clock" was an overclaim.** `SetSystemTime` only printed the
  time. It now sets the device clock (`g_clockOffsetSeconds`, an offset from the
  host clock) that `Local_Date` / `Local_Time` report, so a TimeSynchronization
  or UTCTimeSynchronization moves the Schedule and the Calendar. A sync with an
  unspecified (255) field is ignored. The shared helper's `GetSystemTime` (event
  time stamps, COV lifetimes) stays on the host clock. The `s` demo key adds its
  `Weekly_Schedule` entry at the device clock's "now".
- **`--dcc-password` was advertised but ignored** (`--help`, from `common/`,
  listed it; `main.cpp` compared against a compile-time empty `DCC_PASSWORD`).
  It now sets the password DeviceCommunicationControl and ReinitializeDevice
  require (`g_dccPassword`, default empty), and a start-up line says one is set
  (never what it is).

### Changed

- **Calendar 1 (Cream) is stack-held and Saffron's exception references it.**
  Stack #963, #1758 and #2034 are closed: at this pin the customer header has
  `BACnetStack_AddCalendarObject` / `BACnetStack_AddCalendarDateEntry`, and a
  calendar-reference exception resolves through a stack-held Calendar. Cream's
  `Date_List` is December 25 of every year (previously a hard-coded inline
  2026-12-25 exception with an empty Calendar beside it whose `Present_Value`
  always answered false), the exception uses
  `BACnetStack_AddScheduleExceptionEventWithCalendarReference`, and the stack
  derives Cream's `Present_Value`. README, TODO.md, PICS and `docs/objects.json`
  no longer call it blocked.
- **Stack Pin moved to `6.x` @ `64b2cfac5` (CAS BACnet Stack 6.0.23)** from
  `6.x` @ `abd4cee1` (6.0.21), per the series rule that a pin moves to the latest
  `6.x` whenever an example is updated. No existing call needed changing.
- **`common/` 3.0.0 -> 3.3.0**, copied verbatim from B-SS-CPP `b640a81`. Additive
  for this example: four new keys it does not handle (`k`, `o`, `f`, `p` are
  ignored) and `HelperSendMessage` now sends a broadcast the stack hands it with
  no address.
- **Protocol_Revision 24 -> 30** (the stack's default at the new pin): README,
  AGENTS.md, PICS, `main.cpp` comments.
- **Segmentation is now supported** (`segmented-both`, `Max_Segments_Accepted`
  16, `APDU_Segment_Timeout` 5000 ms): the stack's customer build compiles
  segmentation in from this pin (stack #2992). `docs/PICS.md` section 5 updated;
  section 11 regenerated.
- The `Effective_Period` comment in `main.cpp` said "the current calendar year";
  year 0 makes both bounds open, so the period reads unspecified..unspecified and
  the Schedule is always in effect. Comment corrected; behaviour unchanged.
- README, PICS and version lines: stack 6.0.23, `common/` 3.3.0,
  Protocol_Revision 30, example 1.3.0 (the README still said 1.2.0 and
  `common/` 2.5.0). Sample output shows the `- Unconfirmed:` suffixes `common/`
  prints and the Schedule's first write. Series profile table re-synced.
  APP_VERSION 1.2.2 -> 1.3.0 (minor: behaviour changes above).

### Added

- **Wire Tests** (`tests/`, README "Wire Tests"): `tests/discovery_test.py`
  (copied from B-SS-CPP `da3e96f`, object list adapted) does what a client's
  discovery does - Who-Is, the Device's `Object_List` (control: exactly the
  twelve objects), then every object's `Property_List` and a ReadProperty of
  every listed property - and fails on any Error, Reject, Abort or silence.
  `tests/run_wire_tests.py` runs it; CI runs it on Linux after the smoke test.
  Passes 18/18 (169 reads) on Windows and Linux at the new pin.
- `wiretest/` 0.5.0, the series' shared Wiretest Harness, vendored verbatim
  from B-BBMD-CPP.
- Checked by hand on the wire (Windows, a scratch script, not a committed test):
  at start Saffron 20.0, Cream FALSE, `Date_List` = one Date entry
  (unspecified year, 12, 25, unspecified weekday); after TimeSynchronization to
  2026-12-25 10:00, `Local_Date` reads 2026-12-25, Cream TRUE, Saffron and
  Chartreuse 5.0; to Monday 2026-10-19 09:00, 75.0; to 07:00 the same day, 20.0.

## [1.2.2] - unreleased

### Changed

- **Device renamed from the series' colour placeholder "Rainbow" to "Chipkin
  Example B-AAC"** so devices from different examples in the series are
  distinguishable from each other on the same BACnet network - every example
  previously announced the identical Object_Name "Rainbow", which made two
  examples on one subnet indistinguishable by name. Sub-object names (Analog
  Input 1 "Bronze", etc.) are unchanged - only the Device object's name
  changed. `docs/colour-table.md` (series root) updated to match. APP_VERSION
  bumped 1.2.1 -> 1.2.2.

## [Unreleased]

### Fixed

- **`Application_Software_Version` (12) and `Firmware_Revision` (44) were
  hardcoded and stale** - the same bug found and fixed in the sibling
  BACnetProfileExample-B-SCHUB-CPP example via a real device read (BACnet
  Explorer): `Application_Software_Version` reported a hardcoded `"1.0.0"`
  regardless of the actual build, and `Firmware_Revision` was the same stale
  `"1.0.0"` constant - it was never meant to be this example's own version at
  all, it names the underlying platform. Fixed: `Application_Software_Version`
  now reads `APP_VERSION` directly (one source of truth, can't drift from
  `--version`'s own banner again). `Firmware_Revision` is now built at
  runtime from the CAS BACnet Stack's own `BACnetStack_GetAPIMajorVersion()`/
  `GetAPIMinorVersion()`/`GetAPIPatchVersion()`/`GetAPIBuildVersion()` (the
  same 4 calls `common/CASExampleHelper.cpp`'s `PrintVersion()` already uses
  for the startup banner), populated once right after `LoadBACnetFunctions()`
  succeeds. APP_VERSION bumped 1.2.0 -> 1.2.1.

### Changed

- **Restructured the documentation**: `README.md` is cut down to what this
  example is and how to build/run/verify it; the "Before you ship" table, the
  "Extending the example" material (who-serves-what, adding an object) and the
  full objects-and-properties table moved to a new **TUTORIAL.md**; the
  standalone Protocol Implementation Conformance Statement moved to a new
  **docs/PICS.md** (ANSI/ASHRAE 135 Annex A shape). `docs/objects.json` gained a
  `Device` entry (previously the generated tables omitted the Device object
  entirely) so the PICS's objects-and-properties section now covers all twelve
  objects, not eleven.
- **Build switched from a prebuilt STATIC library to the adapter's default
  SOURCE mode**: `cmake -B build -S .` / `cmake --build build --config Release`
  is now the whole documented build, identically on Windows, Linux and macOS -
  no `tools/build-stack-static.sh` pre-step (that script lives in the
  example-series repository, not this one, so a customer who only has this
  repository never had it). `.github/workflows/release.yml` dropped the
  static-library cache/build steps and the matrix `lib:` entries, configures
  without a link-mode flag, asserts `CAS_BACNET_STACK_LINK` back out as
  `SOURCE` instead of `STATIC`, records `"link_mode": "SOURCE"` in the
  published metrics JSON, and now packages `TUTORIAL.md` and `docs/PICS.md`
  alongside the binary. The Footprint table's numbers were measured from the
  old STATIC build; the next release refreshes them from the SOURCE build.
- `README.md`'s "Versions" callout's `common/` helper version corrected from
  the stale `v2.1.0` to the `v2.5.0` this repository is actually vendoring
  (`COMMON_VERSION` in `common/CASExampleHelper.h`).

## [1.2.0] - 2026-09-15

### Added

- **SCHED-I-B: internal scheduling.** Schedule 1 "Saffron" writes Analog Output 1
  "Chartreuse" `Present_Value` at priority 8, driven by one weekly transition
  (Monday 08:00) and one calendar-date exception (2026-12-25, via
  `BACnetStack_AddScheduleExceptionEventWithCalendarEntry`). Calendar 1 "Cream"
  is added alongside the exception; its `Date_List` cannot be populated through
  the customer API yet (cas-bacnet-stack issue #963 - see `TODO.md`), so the
  exception uses the inline calendar-date form rather than a reference to Cream.
  The `s` key (`common/` 2.1.0's new `KeyCommand::DemoAdvance`) adds a
  `Weekly_Schedule` transition for right now, so the schedule's effect can be
  observed without waiting for the wall clock to reach a seeded time.
- **AE-CRL-B: writable `Recipient_List`.** Notification Class 1 "Crimson"'s
  `Recipient_List` is now registered writable
  (`BACnetStack_SetPropertyWritable`); the stack decodes and stores a
  `WriteProperty` to it itself, and a device-instance recipient written this way
  is resolved via the stack's Device-Address-Binding cache the same way a
  host-seeded one is (cas-bacnet-stack issue #1328).

### Changed

- **`BACnetStack_SetAlarmsAndEventsForObjectEnabled`'s trailing `enabled`
  argument lost its `= true` default in the 6.x interface freeze**; the call
  arming Diamond's alarms now passes it explicitly.
- **`BACnetStack_SendWhoIs`'s `networkType` parameter became
  `networkPortInstance`** (a `uint32_t`); the start-up Who-Is now passes
  `NETWORK_PORT_INSTANCE`.
- **`BACnetStack_AddNetworkPortObjectWithNetworkNumber` is gone**, folded into
  `BACnetStack_AddNetworkPortObject`, which now always takes the network number
  and quality.
- **Every `GetProperty*` callback gained a trailing `uint32_t* errorCode`**
  (cas-bacnet-stack issue #974). Used in exactly one place - State_Text with an
  out-of-range array index now answers `Error(property, invalid-array-index)`
  instead of an empty string - and deliberately left alone on every catch-all
  `return false`, because the decline-and-fabricate fallback is what answers
  required properties this application does not serve.
- Links are identified by Network Port object instance, not network type
  (#822/#556): handled inside `common/`, with a new
  `CASExampleHelper::SetNetworkPortInstance()` call added before
  `RegisterCommonCallbacks()`.
- `BACnetStack_AddRecipientToNotificationClass`, `RegisterCallbackAcknowledgeAlarm`
  and `RegisterCallbackSetSystemTime` had parameter renames only
  (`hundreth`→`hundredth`, `acknowledgement`→`acknowledgment`,
  `year`→`yearMinus1900`); no code change required at these call sites.
- Stack pinned to `6.x` @ `abd4cee1` (reports 6.0.21).
- **Now links the CAS BACnet Stack as a prebuilt STATIC library**
  (`CAS_BACNET_STACK_LINK=STATIC`), built first by `tools/build-stack-static.sh`
  from the stack's own project files. SOURCE and DLL modes remain available in
  the adapter but this example is built and published in STATIC mode only.
- `common/` bumped to **v2.1.0** (see `common/CHANGELOG.md`), byte-identical to
  the other migrated examples; adds `KeyCommand::DemoAdvance` (key `s`).

### Changed (from the earlier unreleased work, folded into this release)

- **Links the CAS BACnet Stack through the `CASBACnetStack::Adapter` CMake target
  instead of compiling its `source/*.cpp` into this project directly.** `main.cpp`
  and `common/CASExampleHelper.cpp` now include `CASBACnetStackAdapter.h` and call
  `LoadBACnetFunctions()` once at the top of `main()`; **every `BACnetStack_*` call
  site is unchanged** — the adapter exposes the same export names in every link
  mode. `CAS_BACNET_STACK_LINK` (`SOURCE` default, or `STATIC`/`DLL`) now picks the
  link mode, so switching is a CMake flag rather than a code change. See the
  README's new "Link modes" section.
  - Stack pinned to `6.x-TestTool` @ `756371c1`, which carries the adapter
    (cas-bacnet-stack PRs #267 and #268).
  - `common/` bumped to **v1.5.1** (see `common/CHANGELOG.md`), byte-identical to
    the other migrated examples. The `LoadBACnetFunctions()` requirement is a
    contract change shared by every example in the series.
  - Release CI now passes `-DCAS_BACNET_STACK_LINK=SOURCE` **explicitly** and
    asserts it back out of `CMakeCache.txt`, so a published artifact stays a
    single self-contained executable even if the CMake default ever moves.
  - README: added parallel-build guidance for the ~600-file first compile and
    refreshed the versions shown.

### Fixed

- **Default device instance is now `389004`, not `389001`.** The series
  device-instance table assigns each profile its own default so that several
  examples can run on one subnet; this example shipped using `389001`, which is
  **B-SS's** instance. Any two of B-SS / B-AAC running together therefore both
  claimed device `389001` — duplicate device instances on a subnet are a BACnet
  conformance problem, and they make discovery ambiguous in exactly the way that
  is hardest to debug (see the SO_REUSEADDR note in the series runbook).
  `--deviceID` still overrides, as BACnet requires.

## [1.0.0] - 2026-06-16

### Added

- Initial **B-AAC (BACnet Advanced Application Controller)** profile example for
  the CAS BACnet Stack in C++. Implements every B-AAC capability the standard stack
  DLL exposes; documents the gaps in [TODO.md](TODO.md).
- Carries the B-ASC object model: Device "Rainbow", read-only inputs (Analog
  "Bronze" / Binary "Emerald" / Multi-State "Hot Pink"), commandable outputs
  (Analog "Chartreuse" / Binary "Fuchsia" / Multi-State "Indigo"), and Network Port
  "Vermilion".
- **Intrinsic alarming (AE-N-I-B):** Analog Value 1 "Diamond" with an OutOfRange
  event algorithm (low/high limit + deadband). Crossing a limit transitions
  `Event_State` and the stack emits an EventNotification.
- **Notification Class 1 "Crimson"** with a seeded recipient (AE-CRL-B, partial). The
  recipient is addressed by BACnet/IP address (defaulting to the local subnet
  broadcast) and receives UNCONFIRMED notifications, because the standard stack's
  notification sender requires a recipient address, not a device instance.
- **AE-ACK-B** (AcknowledgeAlarm callback) and **AE-INFO-B** (GetEventInformation).
- **DS-RPM-B / DS-WPM-B** (ReadPropertyMultiple / WritePropertyMultiple enabled).
- **DM-RD-B** (ReinitializeDevice: accepts COLDSTART/WARMSTART, validates the
  password) and **DM-TS-B / DM-UTC-B** (SetSystemTime callback).
- **DM-DCC-B** carried over from B-ASC; DM-DDB-B / DM-DOB-B discovery; unsolicited
  start-up I-Am to the local subnet.
- A `PasswordAccepted` helper shared by DeviceCommunicationControl and
  ReinitializeDevice (constant-time-style compare).
- All required Protocol_Revision 24 properties across every object; strict build
  warnings on the example's own sources; CMake builds the stack from source.

### Not yet implemented (see [TODO.md](TODO.md))

- **SCHED-I-B** internal scheduling - the standard stack DLL has no Schedule
  execution engine.
- **AE-CRL-B writable Recipient_List** - the recipient list is seeded at start-up,
  not reconfigurable via WriteProperty.

[1.2.0]: https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP/releases/tag/v1.2.0
[1.0.0]: https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP/releases/tag/v1.0.0
