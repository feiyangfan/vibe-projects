# EOS Unlock

A small macOS-focused research project to understand and eventually reproduce the Canon EOS R50 regional/language unlock process without relying on Windows-only service tools.

## Initial target

- Camera: Canon EOS R50
- Region: Japan
- Firmware: 1.1.0
- Host: macOS
- Goal: unlock the full language menu, including Simplified Chinese

## Approach

### 1. Build a safe read-only foundation

Create a minimal `r50tool` for macOS that can:

- Detect the EOS R50 over USB
- Open/close a PTP session
- Read standard device information
- Read Canon EOS vendor-extension information
- Dump advertised operation/property codes
- Log raw request/response traffic
- Refuse all write operations by default

Preferred implementation: C + libusb, with a very small codebase and no dependency on gphoto2 at runtime.

### 2. Identify the Canon service protocol

Research the service path used by tools such as SPT/Tornado for:

- Normal / Factory / Service mode
- Language Lock
- Regional settings
- User Language

Sources may include public Canon PTP research, libgphoto2, CHDK/Magic Lantern history, service documentation, static analysis of legally obtained software/resources, and USB traces from a legitimate service-tool session.

Do **not** guess undocumented write opcodes against the camera.

### 3. Reproduce read-only service queries

Once a service command is understood:

- Add explicit command definitions
- Validate packet format and response parsing
- Test read-only status queries first
- Record model/firmware compatibility

### 4. Add the minimal unlock operation

Only after the protocol is verified:

1. Read current language-lock/region state
2. Back up any relevant service data
3. Disable Language Lock
4. Set regional/user-language data only if required
5. Return the camera to Normal mode
6. Re-read state and verify

Every write must require explicit confirmation and be restricted to known-supported model/firmware combinations.

## Safety rules

- No blind opcode fuzzing
- No firmware flashing as part of this project
- No calibration, shutter-count, serial-number, lens-adjustment, or unrelated EEPROM writes
- No automatic writes on connection
- Keep raw before/after dumps for every persistent change
- Fail closed on unknown model, firmware, response, or payload

## Proposed CLI

```text
r50tool info
r50tool ptp-info
r50tool service-status
r50tool language-status
r50tool dump
r50tool unlock-language
```

The first implementation should expose only the read-only commands.

## Milestones

- [ ] macOS USB/PTP transport
- [ ] R50 identification and device-info dump
- [ ] Canon vendor-operation dump
- [ ] Structured traffic logging
- [ ] Document service-mode findings
- [ ] Identify language-lock read command
- [ ] Implement and verify read-only language status
- [ ] Identify verified unlock write sequence
- [ ] Add guarded unlock command
- [ ] Test on EOS R50 Japan / firmware 1.1.0
