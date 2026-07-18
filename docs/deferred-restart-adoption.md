# Adopting the deferred-restart pattern (DM-RD-B)

How to implement `ReinitializeDevice` in a device built on the CAS BACnet Stack
without breaking the client that asked for the restart.

Applies to any device whose profile includes **DM-RD-B**. In this example series
that is **B-AAC only** — the other seven examples do not register
`RegisterCallbackReinitializeDevice` because their profiles do not include the
BIBB. Do not adopt this into a profile that does not have DM-RD-B; an example
should implement its profile, not a superset of it.

---

## The bug this prevents

`ReinitializeDevice` is a **confirmed** service: the client expects a SimpleACK
before it will consider the request successful.

Returning `true` from the callback does **not** send that ACK. It tells the stack
the request was accepted; the stack then *encodes* the ACK, and the bytes only
reach the wire during a later `BACnetStack_Tick()`.

So this is wrong, however natural it looks:

```cpp
if (reinitializedState == REINITIALIZE_STATE_COLDSTART) {
    PlatformReboot();   // ✗ never returns - the ACK is still sitting in the stack
    return true;        //   unreachable
}
```

The device reboots correctly and the client still reports **timeout / device not
responding**, because no ACK was ever transmitted. From the outside, a device
that obeyed perfectly is indistinguishable from one that ignored the request.
BTL tests for exactly this.

`exit()`, a watchdog reset, and re-running `main()`'s init all fail the same way.

## The fix

Split "accept" from "act":

1. **In the callback** — validate, record that a restart is due at a deadline a
   little in the future, and return `true` immediately.
2. **In the main loop** — once the deadline passes, do the actual restart. By
   then the ACK has been ticked out and the client's own request timer has
   completed cleanly.

The helper in `common/CASExampleHelper.h` implements step 1's bookkeeping:

```cpp
void RequestRestart(RestartKind kind, uint32_t delayMilliseconds);
bool RestartDue(RestartKind* outKind);   // true exactly once, after the deadline
static const uint32_t RESTART_DELAY_MS = 1000;
```

---

## Checklist

- [ ] **Confirm the profile actually includes DM-RD-B.** If it does not, stop —
      do not register the callback.
- [ ] `common/` is at **v1.4.0 or later** (`COMMON_VERSION` in
      `CASExampleHelper.h`). Earlier copies have no `RequestRestart`.
- [ ] Register the callback: `BACnetStack_RegisterCallbackReinitializeDevice(...)`.
- [ ] **Validate the device instance first**, and set `*errorCode` even on that
      path — a `false` return with `*errorCode` untouched ships
      `Error Code = success(84)`, which is meaningless on the wire.
- [ ] **Check the password** (`ERROR_CODE_PASSWORD_FAILURE` on mismatch). Compare
      length first, then all bytes without short-circuiting, so the reply does not
      leak where the password diverged. B-AAC's `PasswordAccepted()` does this and
      is shared with DeviceCommunicationControl.
- [ ] **Reject unsupported states** (2..6 = the backup/restore states) with
      `ERROR_CODE_OPTIONAL_FUNCTIONALITY_NOT_SUPPORTED` — "I don't do that",
      not "bad value" — unless the device genuinely implements backup/restore.
- [ ] On an accepted COLDSTART/WARMSTART: call `RequestRestart(...)` and
      **`return true` without restarting**. Nothing in the callback may reboot,
      `exit()`, block, or sleep.
- [ ] In the main loop, **after `BACnetStack_Tick()`**, call `RestartDue(&kind)`
      and perform the restart there. Placing it before the tick wastes a full
      loop iteration of ACK-transmission time.
- [ ] Handle **both kinds distinctly**. COLDSTART is the full power-on path (all
      objects back to start-up values, all priorities relinquished); WARMSTART
      re-initializes communications while preserving what a warm reboot keeps.
      Treating them identically is a common shortcut and is visible to a client.
- [ ] **Send an I-Am after the restart**, both kinds. Clients that had the device
      bound watch for it to know the restart finished and to re-bind if the
      address moved.
- [ ] On a real device, record **`Last_Restart_Reason`** (`coldstart` /
      `warmstart` / `activate-changes`, per BACnetRestartReason) and
      **`Time_Of_Device_Restart`** as part of the restart. This example does not
      expose those Device properties, so it does not — a shipping device should.
- [ ] If the device persists configuration, decide explicitly what COLDSTART
      wipes versus what survives, and document it. "Coldstart" does not mean
      "factory reset" and clients will not expect it to.

## Verifying it

Behavioural, not compile-time — a build passing proves nothing here.

1. Run the example; note the object values, and command an output to a non-default
   value so a COLDSTART has something visible to clear.
2. Send `ReinitializeDevice(COLDSTART)` with the correct password from a client.
3. **The client must report success, not timeout.** That is the whole test. Watch
   for the SimpleACK to precede the restart log lines.
4. Confirm the restart then happens: the console prints the restart lines, values
   are back at power-on, and an I-Am is broadcast.
5. Repeat with WARMSTART — same ACK behaviour, commanded values preserved.
6. Send with a **wrong** password: expect a `passwordFailure` error and **no**
   restart.
7. Send an unsupported state (e.g. 3): expect
   `optionalFunctionalityNotSupported` and no restart.

## Notes on the helper

- The deadline uses a **monotonic** clock (`GetTickCount64` /
  `CLOCK_MONOTONIC`), never `time()`. A device that supports DM-TS-B can have its
  wall clock stepped — including backwards — by a management station at any
  moment, which with a wall-clock deadline would either fire the restart early or
  strand it in the future.
- Repeat requests during the delay window keep the **earliest** deadline, so a
  second client cannot postpone a restart already promised to the first. A Cold
  request upgrades a pending Warm one; a Warm does not downgrade a pending Cold.
- `RestartDue()` returns true **exactly once** — it clears the request before
  returning. A device that handles the restart in-process (as this example does,
  having no hardware to reset) therefore does not restart again on the next tick.
- One second (`RESTART_DELAY_MS`) is comfortably longer than a tick of the main
  loop. If your loop can stall longer than that — a slow scan cycle, a blocking
  I/O phase — raise the delay to exceed your worst-case tick interval.
