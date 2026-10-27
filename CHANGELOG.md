# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No changes yet._

## [1.5.0] - 2026-10-27

Built on CAS BACnet Stack 6.x (`69b6249f`).

### Added

- **`--deviceName <text>`** sets the Device's Object_Name at start-up, like
  `--deviceID` sets its instance, so two units can be installed together (BACnet
  requires both to be configurable, cl. 12.1.1.3 and 12.1.1.4). The default is
  unchanged (`Chipkin Example B-AAC`). A name must be 1 to 255 bytes with no control
  characters, otherwise the example warns and keeps the default. The name is not
  writable over the network.

### Changed

- **`--xml` works.** The help listed it but the example never read it; each received
  and sent frame now prints as an XML block.
- A ReinitializeDevice START_BACKUP or START_RESTORE (backup and restore are not
  supported) now gets an Error (SERVICES, OPTIONAL_FUNCTIONALITY_NOT_SUPPORTED) instead
  of an Abort, as the standard requires.
- Vendored `common/` updated to 3.5.0 (adds an optional `--deviceName` help line).
- The self-tests' default `--port` is 47829, this example's own port in the series.
- The PICS objects-and-properties block cites the CAS BACnet Stack's property
  profiles; no row changed.

### Fixed

- **Requests no longer go unanswered on Windows**: a request arriving just as the UDP
  receive timed out was silently dropped.
- **PICS corrections**: `Database_Revision` is 12 (the stack counts the objects added at
  start-up, cl. 12.11), and I-Am is marked as executed as well as initiated (DM-DDB-A).

## [1.4.0] - 2026-10-16

Built on CAS BACnet Stack 6.x (`64b2cfac5`, 6.0.23), Protocol_Revision 30. Includes the
changes first developed as 1.2.2 and 1.3.0.

The example now performs the B-AAC Profile Function against a peer (a simulated operator
workstation), and automated tests demonstrate it.

### Added

- **Automated self-tests under `tests/`** for the profile function: alarms to a
  recipient list written over the network, acknowledgment (a stale acknowledgment is
  refused with `invalid-timestamp`), GetEventInformation, a silent recipient, alarms
  redirected to a second workstation, DeviceCommunicationControl, and the schedule.
  `tests/discovery_test.py` reads every property of every object. They run in CI.
- README "The scenario" and "What is Simulation" sections.
- **Segmentation is supported** (`segmented-both`, `Max_Segments_Accepted` 16).
- New documents: `TUTORIAL.md` (extending and reviewing the example) and
  `docs/PICS.md` (the conformance statement).

### Changed

- **The Device is now named "Chipkin Example B-AAC"** (was "Rainbow") so examples on one
  network can be told apart.
- **Protocol_Revision is 30** (was 24).
- **Calendar 1 "Cream" is stack-held**, and Schedule 1 "Saffron"'s exception references
  it. Cream's `Date_List` is December 25 of every year and its `Present_Value` is derived
  by the stack. Before, the exception was an inline date beside an empty Calendar.
- Build documentation uses the adapter's default source mode: `cmake -B build -S .` then
  `cmake --build build --config Release`, on every platform. If you have an older build
  tree, run `cmake -B build` again.
- `common/` updated to 3.4.0: a broadcast addressed to the socket's own address is sent
  to the subnet broadcast.
- The `Effective_Period` comment now says the period is open-ended (unspecified to
  unspecified); behaviour is unchanged.

### Fixed

- **A confirmed alarm to a silent recipient was sent only once.** The device now serves
  `Number_Of_APDU_Retries` 3 (cl. 12.11.29): a recipient that does not SimpleACK gets
  the notification again every `APDU_Timeout` (10 s), three times.
- **Schedule 1 "Saffron" never evaluated.** The schedule and calendar run on the Device's
  `Local_Date` and `Local_Time`, which were not served; both are now, and the schedule
  writes Analog Output 1 as documented (press `s`).
- **A time synchronization now sets the device clock.** Before, TimeSynchronization and
  UTCTimeSynchronization were acknowledged but changed nothing. A sync with an
  unspecified (255) field is ignored.
- **`--dcc-password` was advertised but ignored.** It now sets the password that
  DeviceCommunicationControl and ReinitializeDevice require; a start-up line says one
  is set (never what it is).
- **The AcknowledgeAlarm callback and docs described the wrong check.** The stack runs
  the cl. 13.5.2 procedure itself; the callback now logs who is acknowledging.
- **`Application_Software_Version` and `Firmware_Revision` were hardcoded** to "1.0.0";
  they now report the build's version and the CAS BACnet Stack version.

## [1.2.0] - 2026-09-15

Built on CAS BACnet Stack 6.x (`abd4cee1`, 6.0.21).

### Added

- **SCHED-I-B: internal scheduling.** Schedule 1 "Saffron" writes Analog Output 1
  "Chartreuse" `Present_Value` at priority 8, driven by one weekly transition (Monday
  08:00) and one calendar-date exception (2026-12-25). The `s` key adds a transition for
  right now so the effect can be seen without waiting.
- **AE-CRL-B: writable `Recipient_List`.** Notification Class 1 "Crimson"'s
  `Recipient_List` accepts WriteProperty, and a device-instance recipient written this way
  is resolved from the stack's Device Address Binding cache.
- README sections for the objects and properties, the example series and the footprint;
  releases publish size and start-up metrics.

### Changed

- **The stack is linked through the `CASBACnetStack::Adapter` CMake target.**
  `CAS_BACNET_STACK_LINK` selects `SOURCE`, `STATIC` or `DLL` mode. `common/` updated to
  2.1.0.
- API changes in the 6.x stack that touch the example: every `GetProperty*` callback
  gained a trailing `uint32_t* errorCode` (`State_Text` with an out of range array index
  now returns `invalid-array-index`), `BACnetStack_SendWhoIs` takes a Network Port
  instance, `BACnetStack_AddNetworkPortObjectWithNetworkNumber` is folded into
  `BACnetStack_AddNetworkPortObject`, and
  `BACnetStack_SetAlarmsAndEventsForObjectEnabled` needs its `enabled` argument.

### Fixed

- **The default device instance is now 389004**, not 389001, which belongs to B-SS. Two
  examples on one subnet no longer claim the same instance. `--deviceID` still overrides.

## [1.0.0] - 2026-06-16

### Added

- Initial **B-AAC (BACnet Advanced Application Controller)** profile example for the CAS
  BACnet Stack in C++.
- The B-ASC object model: Device, read-only inputs (Analog, Binary, Multi-State),
  commandable outputs and Network Port.
- **Intrinsic alarming (AE-N-I-B)**: Analog Value 1 "Diamond" with an OutOfRange event
  algorithm; crossing a limit changes `Event_State` and sends an EventNotification.
- **Notification Class 1 "Crimson"** with a seeded recipient (unconfirmed notifications
  to the local subnet broadcast).
- **AE-ACK-B** (AcknowledgeAlarm) and **AE-INFO-B** (GetEventInformation).
- **DS-RPM-B / DS-WPM-B** (ReadPropertyMultiple / WritePropertyMultiple).
- **DM-RD-B** (ReinitializeDevice: COLDSTART and WARMSTART, password checked) and
  **DM-TS-B / DM-UTC-B** (time synchronization).
- **DM-DCC-B**, DM-DDB-B / DM-DOB-B discovery, and an unsolicited I-Am at start-up.
- All required Protocol_Revision 24 properties on every object.

### Known gaps

- SCHED-I-B internal scheduling and a writable AE-CRL-B `Recipient_List` were not yet
  implemented; see `TODO.md`.
