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

        let key: String

        switch page {
        case 0x01:
            key = genericDesktopLabel(usage)

        case 0x07:
            key = keyboardLabel(usage)

        case 0x0C:
            key = consumerLabel(usage)

        default:
            key = String(
                format: "0x%02X:%04X",
                page,
                usage
            )
        }

        return modifierPrefix(modifiers) + key
    }


    private static func modifierPrefix(
        _ mods: UInt8
    ) -> String {
        var result = ""

        if mods & 0x01 != 0 { result += "⌃" }
        if mods & 0x02 != 0 { result += "⇧" }
        if mods & 0x04 != 0 { result += "⌥" }
        if mods & 0x08 != 0 { result += "⌘" }

        // Preserve the existing compact prefix behavior for modified
        // keycodes; standalone right modifiers are labeled separately below.
        if mods & 0x10 != 0 { result += "⌃" }
        if mods & 0x20 != 0 { result += "⇧" }
        if mods & 0x40 != 0 { result += "⌥" }
        if mods & 0x80 != 0 { result += "⌘" }

        return result
    }


    // MARK: - Keyboard / Keypad page (0x07)

    private static func keyboardLabel(
        _ usage: UInt16
    ) -> String {
        // A-Z.
        if usage >= 0x04 && usage <= 0x1D {
            let scalar = UnicodeScalar(
                Int(usage - 0x04) + 65
            )!

            return String(Character(scalar))
        }

        // Number row 1-9.
        if usage >= 0x1E && usage <= 0x26 {
            return String(usage - 0x1D)
        }

        if usage == 0x27 {
            return "0"
        }

        // F1-F12.
        if usage >= 0x3A && usage <= 0x45 {
            return "F\(usage - 0x39)"
        }

        // F13-F24.
        if usage >= 0x68 && usage <= 0x73 {
            return "F\(usage - 0x5B)"
        }

        // Keypad 1-9.
        if usage >= 0x59 && usage <= 0x61 {
            return "KP\(usage - 0x58)"
        }

        // International 1-9.
        if usage >= 0x87 && usage <= 0x8F {
            return "Intl\(usage - 0x86)"
        }

        // Language 1-9.
        if usage >= 0x90 && usage <= 0x98 {
            return "Lang\(usage - 0x8F)"
        }

        switch usage {
        case 0x00: return ""
        case 0x01: return "ErrorRoll"
        case 0x02: return "POSTFail"
        case 0x03: return "Error"

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
        case 0x32: return "Non-US #"
        case 0x33: return ";"
        case 0x34: return "'"
        case 0x35: return "`"
        case 0x36: return ","
        case 0x37: return "."
        case 0x38: return "/"

        case 0x39: return "⇪"

        case 0x46: return "PrtSc"
        case 0x47: return "ScrLk"
        case 0x48: return "Pause"

        case 0x49: return "Ins"
        case 0x4A: return "Home"
        case 0x4B: return "PgUp"
        case 0x4C: return "Del"
        case 0x4D: return "End"
        case 0x4E: return "PgDn"

        case 0x4F: return "→"
        case 0x50: return "←"
        case 0x51: return "↓"
        case 0x52: return "↑"

        case 0x53: return "Num"
        case 0x54: return "KP/"
        case 0x55: return "KP*"
        case 0x56: return "KP-"
        case 0x57: return "KP+"
        case 0x58: return "KP↩"
        case 0x62: return "KP0"
        case 0x63: return "KP."
        case 0x64: return "Non-US \\"
        case 0x65: return "Menu"
        case 0x66: return "Power"
        case 0x67: return "KP="

        case 0x74: return "Execute"
        case 0x75: return "Help"
        case 0x76: return "Menu"
        case 0x77: return "Select"
        case 0x78: return "Stop"
        case 0x79: return "Redo"
        case 0x7A: return "Undo"
        case 0x7B: return "Cut"
        case 0x7C: return "Copy"
        case 0x7D: return "Paste"
        case 0x7E: return "Find"

        case 0x7F: return "Mute"
        case 0x80: return "Vol+"
        case 0x81: return "Vol-"

        case 0x82: return "Lock ⇪"
        case 0x83: return "Lock Num"
        case 0x84: return "Lock Scr"
        case 0x85: return "KP,"
        case 0x86: return "KP="

        case 0x99: return "AltErase"
        case 0x9A: return "SysReq"
        case 0x9B: return "Cancel"
        case 0x9C: return "Clear"
        case 0x9D: return "Prior"
        case 0x9E: return "Return"
        case 0x9F: return "Separator"
        case 0xA0: return "Out"
        case 0xA1: return "Oper"
        case 0xA2: return "Clear"
        case 0xA3: return "CrSel"
        case 0xA4: return "ExSel"

        case 0xB0: return "KP00"
        case 0xB1: return "KP000"
        case 0xB2: return "Thousands"
        case 0xB3: return "Decimal"
        case 0xB4: return "Currency"
        case 0xB5: return "Subunit"
        case 0xB6: return "KP("
        case 0xB7: return "KP)"
        case 0xB8: return "KP{"
        case 0xB9: return "KP}"
        case 0xBA: return "KP Tab"
        case 0xBB: return "KP⌫"

        case 0xE0: return "⌃"
        case 0xE1: return "⇧"
        case 0xE2: return "⌥"
        case 0xE3: return "⌘"
        case 0xE4: return "R⌃"
        case 0xE5: return "R⇧"
        case 0xE6: return "R⌥"
        case 0xE7: return "R⌘"

        default:
            return String(
                format: "Key %02X",
                usage
            )
        }
    }


    // MARK: - Consumer page (0x0C)

    private static func consumerLabel(
        _ usage: UInt16
    ) -> String {
        switch usage {
        // Display / brightness.
        case 0x006F: return "Bri+"
        case 0x0070: return "Bri-"
        case 0x0071: return "Brightness"
        case 0x0072: return "Bklt"
        case 0x0073: return "Bri Min"
        case 0x0074: return "Bri Max"
        case 0x0075: return "Bri Auto"

        // Media transport.
        case 0x00B0: return "▶"
        case 0x00B1: return "⏸"
        case 0x00B2: return "●"
        case 0x00B3: return "⏩"
        case 0x00B4: return "⏪"
        case 0x00B5: return "⏭"
        case 0x00B6: return "⏮"
        case 0x00B7: return "⏹"
        case 0x00B8: return "Eject"
        case 0x00BC: return "Repeat"
        case 0x00CD: return "⏯"

        // Audio.
        case 0x00E2: return "Mute"
        case 0x00E9: return "Vol+"
        case 0x00EA: return "Vol-"

        // Common application launch controls.
        case 0x0183: return "Media"
        case 0x018A: return "Mail"
        case 0x0192: return "Calc"
        case 0x0194: return "Files"

        // Common browser/application controls.
        case 0x0221: return "Search"
        case 0x0223: return "Home"
        case 0x0224: return "Back"
        case 0x0225: return "Forward"
        case 0x0226: return "Stop"
        case 0x0227: return "Refresh"
        case 0x022A: return "Bookmarks"

        default:
            return String(
                format: "Consumer %04X",
                usage
            )
        }
    }


    // MARK: - Generic Desktop page (0x01)

    private static func genericDesktopLabel(
        _ usage: UInt16
    ) -> String {
        switch usage {
        case 0x0081: return "Power"
        case 0x0082: return "Sleep"
        case 0x0083: return "Wake"

        default:
            return String(
                format: "Desktop %04X",
                usage
            )
        }
    }
}
