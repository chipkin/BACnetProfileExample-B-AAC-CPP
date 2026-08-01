# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - unreleased

> Not tagged yet: `v1.0.0` is the only tag in this repository. `release.yml` publishes binaries on a `v*.*.*`
> tag, so until that tag exists this section describes what is on the
> branch, not what shipped.

### Changed

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
- **Notification Class 1 "Jade"** with a seeded recipient (AE-CRL-B, partial). The
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

[1.0.0]: https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP/releases/tag/v1.0.0
