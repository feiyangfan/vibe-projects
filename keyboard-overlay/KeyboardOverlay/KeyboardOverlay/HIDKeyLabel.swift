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
        let page = UInt8((value >> 16) & 0xFF)
        let usage = UInt16(value & 0xFFFF)

        var key: String

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
        case 0x2A: return "⌫"
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
