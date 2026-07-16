# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - unreleased

> Not tagged yet: `v1.0.0` is the only tag in this repository. `release.yml` publishes binaries on a `v*.*.*`
> tag, so until that tag exists this section describes what is on the
> branch, not what shipped.

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

[Unreleased]: https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP/releases/tag/v1.0.0
