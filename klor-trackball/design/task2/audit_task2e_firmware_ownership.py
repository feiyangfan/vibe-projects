#!/usr/bin/env python3
"""Task 2E: freeze QMK firmware ownership for the KLOR trackball variant.

Read-only audit over the stock KLOR QMK sources plus fresh Task 2D evidence.
It identifies every stock feature that currently claims a target PMW GPIO and
defines the revision-1 firmware ownership contract without editing production
firmware in Task 2.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QMK = ROOT / "klor1.4/FIRMWARE/qmk_rp2040/electronlab/klor"
CONFIG = QMK / "config.h"
KEYBOARD_JSON = QMK / "keyboard.json"
RULES = QMK / "rules.mk"
HALCONF = QMK / "halconf.h"
MCUCONF = QMK / "mcuconf.h"
DEFAULT_CONFIG = QMK / "keymaps/default/config.h"
DEFAULT_RULES = QMK / "keymaps/default/rules.mk"
VIAL_CONFIG = QMK / "keymaps/vial/config.h"
VIAL_RULES = QMK / "keymaps/vial/rules.mk"
DEFAULT_2D = ROOT / "design/task2/generated/task2d-pcb-net-contract-audit.json"

TARGET_FEATURES = {
    "bootmagic": True,
    "encoder": True,
    "extrakey": True,
    "haptic": False,
    "mousekey": False,
    "oled": False,
    "pointing_device": True,
    "rgb_matrix": True,
    "audio": False,
}

TARGET_PINS = {
    "GP0": "RGB-WS2812",
    "GP1": "split-half-duplex-serial",
    "GP2": "PMW3360-SCK",
    "GP3": "PMW3360-MOSI",
    "GP4": "PMW3360-MISO",
    "GP5": "matrix-row",
    "GP6": "matrix-row",
    "GP7": "matrix-row",
    "GP8": "matrix-row",
    "GP9": "PMW3360-CS",
    "GP20": "matrix-column",
    "GP21": "matrix-column",
    "GP22": "matrix-column",
    "GP23": "matrix-column",
    "GP26": "matrix-column",
    "GP27": "matrix-column",
    "GP28": "encoder",
    "GP29": "encoder",
}

TARGET_QMK = {
    "pointing_device_driver": "pmw3360",
    "split_pointing": True,
    "pointing_device_side": "right",
    "spi_driver": "SPID0",
    "spi_sck_pin": "GP2",
    "spi_mosi_pin": "GP3",
    "spi_miso_pin": "GP4",
    "pmw33xx_cs_pin": "GP9",
    "motion_pin": None,
    "serial_tx_pin": "GP1",
    "serial_mode": "half-duplex",
    "handedness": "EE_HANDS",
    "auto_mouse_revision1": False,
}

TARGET_HAL = {
    "HAL_USE_SPI": "TRUE",
    "HAL_USE_I2C": "FALSE",
    "HAL_USE_PWM": "FALSE",
    "RP_SPI_USE_SPI0": "TRUE",
    "RP_SPI_USE_SPI1": "FALSE",
    "RP_I2C_USE_I2C1": "FALSE",
    "RP_PWM_USE_PWM4": "FALSE",
}


def defines(text: str, name: str, commented: bool = False) -> list[str]:
    out = []
    for line in text.splitlines():
        if commented:
            m = re.match(r"\s*//\s*#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", line)
        else:
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            m = re.match(r"#\s*define\s+" + re.escape(name) + r"(?:\s+(.+))?$", stripped)
        if m:
            out.append((m.group(1) or "true").strip())
    return out


def make_assignments(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r"([A-Za-z0-9_]+)\s*[:?+]?=\s*(.*?)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def c_defines(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        m = re.match(r"#\s*define\s+([A-Za-z0-9_]+)(?:\s+(.+))?$", stripped)
        if m:
            out[m.group(1)] = (m.group(2) or "true").strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task2d-json", type=Path, default=DEFAULT_2D)
    ap.add_argument("--json-output", type=Path)
    args = ap.parse_args()

    two_d = json.loads(args.task2d_json.read_text(encoding="utf-8"))
    keyboard = json.loads(KEYBOARD_JSON.read_text(encoding="utf-8"))
    config = CONFIG.read_text(encoding="utf-8")
    rules = make_assignments(RULES.read_text(encoding="utf-8"))
    hal = c_defines(HALCONF.read_text(encoding="utf-8"))
    mcu = c_defines(MCUCONF.read_text(encoding="utf-8"))
    default_config = DEFAULT_CONFIG.read_text(encoding="utf-8")
    vial_config = VIAL_CONFIG.read_text(encoding="utf-8")
    default_rules = make_assignments(DEFAULT_RULES.read_text(encoding="utf-8"))
    vial_rules = make_assignments(VIAL_RULES.read_text(encoding="utf-8"))

    stock = {
        "features": keyboard.get("features", {}),
        "matrix_cols": keyboard.get("matrix_pins", {}).get("cols", []),
        "matrix_rows": keyboard.get("matrix_pins", {}).get("rows", []),
        "encoder_left": keyboard.get("encoder", {}).get("rotary", []),
        "encoder_right": keyboard.get("split", {}).get("encoder", {}).get("right", {}).get("rotary", []),
        "ws2812_pin": keyboard.get("ws2812", {}).get("pin"),
        "split_sync": keyboard.get("split", {}).get("transport", {}).get("sync", {}),
        "config_claims": {
            "I2C1_SDA_PIN": defines(config, "I2C1_SDA_PIN"),
            "I2C1_SCL_PIN": defines(config, "I2C1_SCL_PIN"),
            "SERIAL_USART_TX_PIN": defines(config, "SERIAL_USART_TX_PIN"),
            "SERIAL_USART_TX_PIN_COMMENTED": defines(config, "SERIAL_USART_TX_PIN", commented=True),
            "SERIAL_USART_RX_PIN_COMMENTED": defines(config, "SERIAL_USART_RX_PIN", commented=True),
            "SERIAL_USART_FULL_DUPLEX_COMMENTED": defines(config, "SERIAL_USART_FULL_DUPLEX", commented=True),
            "AUDIO_PIN": defines(config, "AUDIO_PIN"),
            "PAW3204_SCLK_PIN": defines(config, "PAW3204_SCLK_PIN"),
            "PAW3204_SDIO_PIN": defines(config, "PAW3204_SDIO_PIN"),
        },
        "keyboard_rules": rules,
        "halconf": hal,
        "mcuconf": mcu,
        "default_keymap_rules": default_rules,
        "vial_keymap_rules": vial_rules,
        "default_ee_hands": bool(defines(default_config, "EE_HANDS")),
        "vial_ee_hands": bool(defines(vial_config, "EE_HANDS")),
    }

    contract_by_pin = {row["connector_pin"]: row for row in two_d.get("contract", [])}

    checks = {
        "task2d_dependency_passes": bool(two_d.get("checks")) and all(two_d["checks"].values()),
        "task2d_spi_gpio_contract_matches": (
            contract_by_pin.get(1, {}).get("mcu_gpio") == "GP9"
            and contract_by_pin.get(2, {}).get("mcu_gpio") == "GP4"
            and contract_by_pin.get(3, {}).get("mcu_gpio") == "GP3"
            and contract_by_pin.get(4, {}).get("mcu_gpio") == "GP2"
            and contract_by_pin.get(5, {}).get("mcu_gpio") is None
        ),
        "stock_rgb_pin_gp0": stock["ws2812_pin"] == "GP0",
        "stock_split_tx_gp1": stock["config_claims"]["SERIAL_USART_TX_PIN"] == ["GP1     // USART TX pin"],
        "stock_matrix_rows_preserved": stock["matrix_rows"] == ["GP5", "GP6", "GP7", "GP8"],
        "stock_matrix_cols_preserved": stock["matrix_cols"] == ["GP27", "GP26", "GP22", "GP20", "GP23", "GP21"],
        "stock_encoder_left_preserved": stock["encoder_left"] == [{"pin_a": "GP28", "pin_b": "GP29"}],
        "stock_encoder_right_preserved": stock["encoder_right"] == [{"pin_a": "GP29", "pin_b": "GP28"}],
        "stock_i2c_conflict_gp2_gp3_present": (
            stock["config_claims"]["I2C1_SDA_PIN"] == ["GP2"]
            and stock["config_claims"]["I2C1_SCL_PIN"] == ["GP3"]
        ),
        "stock_paw3204_conflict_gp2_gp3_present": (
            stock["config_claims"]["PAW3204_SDIO_PIN"] == ["GP2"]
            and stock["config_claims"]["PAW3204_SCLK_PIN"] == ["GP3"]
        ),
        "stock_audio_conflict_gp9_present": stock["config_claims"]["AUDIO_PIN"] == ["GP9"],
        "stock_full_duplex_gp4_option_documented": any(v.startswith("GP4") for v in stock["config_claims"]["SERIAL_USART_TX_PIN_COMMENTED"]),
        "stock_pointing_device_disabled": stock["features"].get("pointing_device") is False,
        "stock_oled_haptic_audio_enabled": (
            stock["features"].get("oled") is True
            and stock["features"].get("haptic") is True
            and stock["features"].get("audio") is True
        ),
        "stock_default_keymap_reenables_conflicting_features": all(
            default_rules.get(k) == "yes"
            for k in ("OLED_ENABLE", "AUDIO_ENABLE", "HAPTIC_ENABLE")
        ),
        "stock_vial_keymap_reenables_conflicting_features": all(
            vial_rules.get(k) == "yes"
            for k in ("OLED_ENABLE", "AUDIO_ENABLE", "HAPTIC_ENABLE")
        ),
        "ee_hands_present_in_default_and_vial": stock["default_ee_hands"] and stock["vial_ee_hands"],
        "spi_hal_already_enabled": hal.get("HAL_USE_SPI") == "TRUE",
        "spi0_already_enabled": mcu.get("RP_SPI_USE_SPI0") == "TRUE",
        "stock_i2c1_currently_enabled": hal.get("HAL_USE_I2C") == "TRUE" and mcu.get("RP_I2C_USE_I2C1") == "TRUE",
        "stock_pwm4_currently_enabled_for_audio": hal.get("HAL_USE_PWM") == "TRUE" and mcu.get("RP_PWM_USE_PWM4") == "TRUE",
        "target_gpio_owners_unique": len(TARGET_PINS) == len(set(TARGET_PINS)),
        "target_spi_pins_match_task2d": (
            TARGET_QMK["spi_sck_pin"] == contract_by_pin[4]["mcu_gpio"]
            and TARGET_QMK["spi_mosi_pin"] == contract_by_pin[3]["mcu_gpio"]
            and TARGET_QMK["spi_miso_pin"] == contract_by_pin[2]["mcu_gpio"]
            and TARGET_QMK["pmw33xx_cs_pin"] == contract_by_pin[1]["mcu_gpio"]
        ),
        "target_motion_pin_unused": TARGET_QMK["motion_pin"] is None,
        "target_right_only_pointing": TARGET_QMK["split_pointing"] and TARGET_QMK["pointing_device_side"] == "right",
        "target_no_i2c_or_audio_peripheral_ownership": (
            TARGET_HAL["HAL_USE_I2C"] == "FALSE"
            and TARGET_HAL["RP_I2C_USE_I2C1"] == "FALSE"
            and TARGET_HAL["HAL_USE_PWM"] == "FALSE"
            and TARGET_HAL["RP_PWM_USE_PWM4"] == "FALSE"
        ),
    }

    report = {
        "task": "2E",
        "sources": {
            "task2d_json": str(args.task2d_json),
            "config_h": str(CONFIG.relative_to(ROOT)),
            "keyboard_json": str(KEYBOARD_JSON.relative_to(ROOT)),
            "rules_mk": str(RULES.relative_to(ROOT)),
            "halconf_h": str(HALCONF.relative_to(ROOT)),
            "mcuconf_h": str(MCUCONF.relative_to(ROOT)),
            "default_keymap_config": str(DEFAULT_CONFIG.relative_to(ROOT)),
            "default_keymap_rules": str(DEFAULT_RULES.relative_to(ROOT)),
            "vial_keymap_config": str(VIAL_CONFIG.relative_to(ROOT)),
            "vial_keymap_rules": str(VIAL_RULES.relative_to(ROOT)),
        },
        "stock": stock,
        "target": {
            "features": TARGET_FEATURES,
            "pin_ownership": TARGET_PINS,
            "qmk": TARGET_QMK,
            "hal_mcu": TARGET_HAL,
            "rgb": {
                "pin": "GP0",
                "left_count": 20,
                "right_count": 19,
                "total_count": 39,
                "note": "mapping implementation remains Task 7; Task 2E freezes ownership/count only",
            },
            "matrix": {
                "rows": ["GP5", "GP6", "GP7", "GP8"],
                "cols": ["GP27", "GP26", "GP22", "GP20", "GP23", "GP21"],
                "removed_position": [7, 1],
            },
            "encoder": {
                "left": {"pin_a": "GP28", "pin_b": "GP29"},
                "right": {"pin_a": "GP29", "pin_b": "GP28"},
            },
            "implementation_rules": [
                "use a trackball-specific firmware derivative; do not overwrite stock KLOR firmware",
                "enable pointing device with PMW3360 driver",
                "enable split pointing and declare the single pointing device on the right",
                "preserve EE_HANDS so QMK can identify the right sensor half",
                "explicitly override SPI0 pins to GP2/GP3/GP4 and CS to GP9",
                "do not define POINTING_DEVICE_MOTION_PIN for revision 1",
                "remove/omit the PAW3204 POINTING_DEVICE_ENABLE block from the trackball variant",
                "disable OLED, haptic, audio, music, I2C ownership and their keymap-level re-enables",
                "remove I2C_DRIVER_REQUIRED and audio driver ownership from the trackball variant",
                "keep GP1 half-duplex serial, GP0 RGB, matrix pins and encoder pins unchanged",
                "leave pointer rotation/inversion and CPI tuning for Task 7 bring-up",
                "leave auto-mouse disabled for revision-1 base bring-up unless explicitly added later",
            ],
        },
        "checks": checks,
    }

    output = json.dumps(report, indent=2, sort_keys=True)
    print(output)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(output + "\n", encoding="utf-8")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
