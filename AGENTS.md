# AGENTS.md

Guidance for AI coding agents working in this repository. See
<https://agents.md/> for the format. Human contributors should read
[README.md](README.md) first.

## What this project is

A **tutorial** C++ example that implements **as much of** the BACnet **B-AAC
(Advanced Application Controller)** profile as the standard CAS BACnet Stack DLL
supports. It is one of a series - one git repo per BACnet profile - and builds on
B-ASC by adding ReadPropertyMultiple/WritePropertyMultiple, **intrinsic alarming**
(AE-N-I-B / AE-ACK-B / AE-INFO-B), time synchronisation, and ReinitializeDevice.
What B-AAC requires but the stack cannot yet do (notably SCHED-I-B internal
scheduling) is documented in [TODO.md](TODO.md) - keep that file honest and current.
The top priority is that the code reads like a tutorial a customer can learn from
and copy-paste. Favour clarity over cleverness.

## Layout

This repository is self-contained:

- `main.cpp` - the example device.
- `common/` - the shared helper (vendored).
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack** as a git submodule
  (private; compiled from source). After cloning, run
  `git submodule update --init --recursive`.

## Build

```bash
git submodule update --init --recursive   # once, if not cloned with --recursive
cmake -B build -S .
cmake --build build --config Release
```

The first build compiles the whole stack (~460 files) and takes a few minutes;
later incremental builds are fast. Use `-D CAS_STACK_DIR=...` only if your stack
lives outside the bundled submodule.

## Run

```bash
./build/BACnetExampleBAAC [--port 47808] [--deviceID 389001]   # Linux/macOS
.\build\Release\BACnetExampleBAAC.exe [--port 47808] [--deviceID 389001]   # Windows
```

Interactive keys while running: `h` help, `q` quit, up/down nudge Analog Input 1.

## Conventions

- Device is named "Rainbow"; objects use the series' colour names; vendor id 389.
- Implement the B-AAC services the stack supports; expose **every required
  property** of each object for Protocol_Revision 24. Anything B-AAC requires that
  is NOT implemented must be listed in [TODO.md](TODO.md) and the README.
- Intrinsic alarming: arm an object with `SetIntrinsic*Algorithm` + a Notification
  Class (`AddNotificationClassObject` + `AddRecipientToNotificationClass`) +
  `SetAlarmsAndEventsForObjectEnabled`. Drive the monitored Present_Value and call
  `BACnetStack_UpdateValue` so the stack re-evaluates and fires the notification.
  The recipient must be addressed by ADDRESS (the device-instance form is not
  implemented by the standard stack's notification sender).
- Outputs are **commandable**: store the 16-slot `Priority_Array` +
  `Relinquish_Default` in the app (the `Commandable` struct); let the stack
  resolve `Present_Value`. Writes land via the `SetProperty*` callbacks (value)
  and `SetPropertyNull` (relinquish).
- DeviceCommunicationControl (DM-DCC-B): the stack runs the enable/disable state
  machine; the `DeviceCommunicationControl` callback just validates `DCC_PASSWORD`
  and logs. The deprecated plain `disable` (1) is rejected by the stack at
  Protocol_Revision >= 20 - only `enable` (0) and `disable-initiation` (2) apply.
- Match the surrounding code style: `const`-correct parameters, check every stack
  return value, keep `main.cpp` linear and well-commented.
- Do **not** edit `../common` from this repo - it is shared across all examples
  and has a single source of truth.

## How to verify a change

There are no unit tests; verification is behavioural:

1. Build, then run one instance on a clear UDP port.
2. With a BACnet client (e.g. the CAS BACnet Explorer), send **Who-Is** and
   confirm **I-Am** from the device instance.
3. **ReadProperty** every required property of every object and confirm the
   values; confirm `Protocol_Revision` is 24 and `Object_List` lists all objects.
4. **WriteProperty** a commandable output's `Present_Value` at a priority, re-read
   it (and its `Priority_Array`), then write NULL to relinquish and confirm it
   falls back to `Relinquish_Default`. Confirm a write to a read-only input is
   rejected.
5. **Alarming**: WriteProperty Analog Value 1 "Diamond" `Present_Value` above the
   high limit; confirm `Event_State` goes to `high-limit` and an EventNotification
   is sent (check the device log / a listener); write it back and confirm `NORMAL`.
6. **Device management**: ReinitializeDevice WARMSTART SimpleACKs; DCC
   `disable-initiation`/`enable` SimpleACK; a wrong password (if set) is rejected.

Verification is manual (no in-repo test suite ships). During development a
raw-socket smoke script was used against a running instance on a clear `--port`
(mind the SO_REUSEADDR gotcha - kill stale instances first).

## Releasing

Bump `APP_VERSION` in `main.cpp` and add an entry to [CHANGELOG.md](CHANGELOG.md),
then tag `vX.Y.Z`. The GitHub Actions workflow builds and publishes the release.

## License

The example source code is dedicated to the public domain under
[CC0-1.0](LICENSE). The CAS BACnet Stack is a separate, commercially licensed
product and is not covered by that dedication.
