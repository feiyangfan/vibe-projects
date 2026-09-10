//
//  HIDKeyLabel.swift
//  KeyboardOverlay
//
//  Created by Feiyang Fan on 2026-08-18.
//

import Foundation

enum HIDKeyLabel {

    static func label(for value: UInt32) -> String {
        let modifiers = UInt8((value >> 24) & 0xFF)
        var page = UInt8((value >> 16) & 0xFF)
        let usage = UInt16(value & 0xFFFF)

        // ZMK may encode keyboard usages with page 0 in some contexts.
        if page == 0 {
            page = 0x07
        }

        /*
         * For printable keyboard keys, render Shift as the character it
         * actually produces on a US keyboard instead of showing "⇧" plus
         * the unshifted key.
         *
         * Examples:
         *   LS(N1)   -> !
         *   RS(N2)   -> @
         *   LS(LBKT) -> {
         *   LS(SQT)  -> "
         *
         * If other modifiers are present, keep them:
         *   LCTRL + LSHIFT + N1 -> ⌃!
         *
         * Standalone modifier keys (LSHIFT/RSHIFT) are unaffected because
         * those are HID usages 0xE1/0xE5 rather than encoded modifier bits.
         */
        if page == 0x07,
           hasShift(modifiers),
           let shifted = shiftedUSKeyboardLabel(usage) {

            let modifiersWithoutShift =
                modifiers & ~UInt8(0x22) // LSHIFT | RSHIFT

            return modifierPrefix(modifiersWithoutShift) + shifted
        }

        let key: String

        switch page {
        case 0x07:
            key = keyboardLabel(usage)

        case 0x0C:
            key = "Consumer \(usage)"

        default:
            key = String(
                format: "0x%02X:%04X",
                page,
                usage
            )
        }

        return modifierPrefix(modifiers) + key
    }

    private static func hasShift(_ mods: UInt8) -> Bool {
        // HID modifier bitmap:
        // bit 1 = Left Shift, bit 5 = Right Shift.
        (mods & 0x22) != 0
    }

    private static func shiftedUSKeyboardLabel(
        _ usage: UInt16
    ) -> String? {
        /*
         * US keyboard shifted printable keys.
         *
         * Letters are intentionally included. The normal overlay already
         * renders alphabetic key labels uppercase, so LS(A) becomes "A"
         * rather than the less useful "⇧A".
         */

        // A–Z: HID usages 0x04–0x1D.
        if usage >= 0x04 && usage <= 0x1D {
            let scalar = UnicodeScalar(
                Int(usage - 0x04) + 65
            )!

            return String(Character(scalar))
        }

        switch usage {
        // Number row.
        case 0x1E: return "!"
        case 0x1F: return "@"
        case 0x20: return "#"
        case 0x21: return "$"
        case 0x22: return "%"
        case 0x23: return "^"
        case 0x24: return "&"
        case 0x25: return "*"
        case 0x26: return "("
        case 0x27: return ")"

        // Punctuation.
        case 0x2D: return "_"
        case 0x2E: return "+"
        case 0x2F: return "{"
        case 0x30: return "}"
        case 0x31: return "|"
        case 0x33: return ":"
        case 0x34: return "\""
        case 0x35: return "~"
        case 0x36: return "<"
        case 0x37: return ">"
        case 0x38: return "?"

        default:
            return nil
        }
    }

    private static func modifierPrefix(_ mods: UInt8) -> String {
        var result = ""

        if mods & 0x01 != 0 { result += "⌃" }
        if mods & 0x02 != 0 { result += "⇧" }
        if mods & 0x04 != 0 { result += "⌥" }
        if mods & 0x08 != 0 { result += "⌘" }

        if mods & 0x10 != 0 { result += "⌃" }
        if mods & 0x20 != 0 { result += "⇧" }
        if mods & 0x40 != 0 { result += "⌥" }
        if mods & 0x80 != 0 { result += "⌘" }

        return result
    }

    private static func keyboardLabel(_ usage: UInt16) -> String {
        // A–Z: HID usages 0x04–0x1D
        if usage >= 0x04 && usage <= 0x1D {
            let scalar = UnicodeScalar(
                Int(usage - 0x04) + 65
            )!

            return String(Character(scalar))
        }

        // 1–9
        if usage >= 0x1E && usage <= 0x26 {
            return String(usage - 0x1D)
        }

        if usage == 0x27 {
            return "0"
        }

        switch usage {
        case 0x28: return "↩"
        case 0x29: return "Esc"
        case /Users/feiyangfan/Developer/keyboard/zmk-config-totem/config/boards/shields/totem/totem.keymap0x2A: return "⌫"
        case 0x2B: return "Tab"
        case 0x2C: return "Space"

        case 0x2D: return "-"
        case 0x2E: return "="
        case 0x2F: return "["
        case 0x30: return "]"
        case 0x31: return "\\"
        case 0x33: return ";"
        case 0x34: return "'"
        case 0x35: return "`"
        case 0x36: return ","
        case 0x37: return "."
        case 0x38: return "/"
        case 0x39:
            return "⇪"

        case 0x4F: return "→"
        case 0x50: return "←"
        case 0x51: return "↓"
        case 0x52: return "↑"

        case 0xE0: return "⌃"
        case 0xE1: return "⇧"
        case 0xE2: return "⌥"
        case 0xE3: return "⌘"
        case 0xE4: return "R⌃"
        case 0xE5: return "R⇧"
        case 0xE6: return "R⌥"
        case 0xE7: return "R⌘"

        default:
            return String(format: "Key %02X", usage)
        }
    }
}
