# EOS Unlock

A macOS-focused research project for understanding the Canon EOS R50 regional/language lock and, only after the protocol is verified, reproducing the minimum safe unlock operation without Windows-only service software.

## Target

- Camera: Canon EOS R50
- Region: Japan
- Known test firmware: 1.1.0
- Host: macOS
- Long-term goal: expose the full language menu, including Simplified Chinese

## Current status: v0.1 read-only foundation

The repository now contains `r50tool`, a small C/libusb PTP client. v0.1 intentionally implements only non-persistent foundation operations:

- Discover a Canon USB still-image/PTP interface
- Read standard PTP `DeviceInfo`
- Refuse the device unless it identifies as `Canon EOS R50`
- Open and close a PTP session
- List the camera-advertised operation, event, and property codes
- Hex-dump raw PTP command/data/response containers with `--trace`
- Hard-reject every opcode except the reviewed read-only/session allowlist
- Query Canon `EOS_GetDeviceInfoEx (0x9108)` to enumerate extended EOS event/property/capability IDs

There is **no language unlock or arbitrary-opcode command in v0.1**.

## Build on macOS

Install the build dependencies with Homebrew:

```bash
brew install libusb pkg-config
```

Then:

```bash
cd eos-unlock
make
```

The output binary is `./r50tool`.

## Camera setup

1. Use a USB-C cable that supports data.
2. Put the R50 USB connection mode in the normal photo-import/remote-control mode.
3. Close EOS Utility, Photos, Image Capture, and other software that may own the camera.
4. Connect and power on the R50.

If macOS has already claimed the PTP interface, `r50tool` will fail rather than trying to forcefully detach another process.

## Usage

```text
./r50tool info
./r50tool ptp-info
./r50tool eos-info
./r50tool dump
./r50tool --trace dump 2> r50-trace.log
./r50tool --trace eos-info > r50-eos-info.txt 2> r50-eos-trace.log
```

`info` prints identity and PTP version information. `ptp-info` prints the operation/event/property codes advertised by standard DeviceInfo. `eos-info` performs the reviewed read-only Canon `0x9108` query and prints its extended 32-bit event/property/capability arrays. `dump` prints standard identity and capabilities. `--trace` writes raw PTP container bytes to stderr. Trace/dump output can contain the camera serial number, so treat captured files as device-identifying data.

A useful first run is:

```bash
./r50tool --trace dump > r50-dump.txt 2> r50-trace.log
```

## Architecture

```text
macOS
  -> libusb
    -> USB Still Image/PTP interface
      -> standard PTP containers
        -> Canon EOS R50
```

`src/ptp.c` owns USB/PTP transport and DeviceInfo parsing. `src/main.c` is deliberately small and exposes only the read-only CLI surface.

## Next protocol-research phase

The missing information is the Canon service protocol used for:

- Normal / Factory / Service mode
- Language Lock
- Regional settings
- User Language

Potential evidence sources include public Canon PTP research, libgphoto2, CHDK/Magic Lantern history, service documentation, static analysis of legitimately obtained service-tool resources, and USB traces from a legitimate service-tool session.

Do **not** infer a write command merely because an unknown Canon opcode is advertised by the camera.

## Safety rules

- No blind opcode fuzzing
- No arbitrary opcode CLI
- No firmware flashing
- No calibration, serial-number, shutter-count, lens-adjustment, or unrelated EEPROM writes
- No automatic persistent writes on connection
- Keep raw before/after dumps for every future persistent change
- Fail closed on unknown model, firmware, response, or payload
- Add write support only after the exact command and payload semantics are independently understood

## Proposed future CLI

```text
r50tool service-status
r50tool language-status
r50tool unlock-language
```

These commands are intentionally **not implemented** yet.

## Milestones

- [x] macOS USB/PTP transport
- [x] R50 identification and DeviceInfo dump
- [x] Canon vendor-operation dump
- [x] Structured raw PTP traffic logging
- [ ] Validate v0.1 against the Japanese EOS R50 / firmware 1.1.0 hardware
- [x] Query Canon EOS extended DeviceInfo (0x9108) in read-only mode
- [ ] Inspect R50 1.1.0 extended property/capability IDs for language/region clues
- [ ] Document service-mode findings
- [ ] Identify language-lock read command
- [ ] Implement and verify read-only language status
- [ ] Identify verified unlock write sequence
- [ ] Add guarded unlock command
- [ ] Verify unlock on EOS R50 Japan / firmware 1.1.0
