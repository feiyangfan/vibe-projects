//
//  FrameCodec.swift
//  KeyboardOverlay
//
//  Created by Feiyang Fan on 2026-08-18.
//

import Foundation

final class FrameCodec {
    static let start: UInt8 = 0xAB
    static let escape: UInt8 = 0xAC
    static let end: UInt8 = 0xAD

    // MARK: - Encode

    static func encode(_ payload: Data) -> Data {
        var output = Data([start])

        for byte in payload {
            if byte == start || byte == escape || byte == end {
                output.append(escape)
            }

            output.append(byte)
        }

        output.append(end)

        return output
    }

    // MARK: - Decode

    private var buffer = Data()
    private var receivingFrame = false
    private var escaped = false

    var onFrame: ((Data) -> Void)?

    func feed(_ data: Data) {
        for byte in data {
            if !receivingFrame {
                if byte == Self.start {
                    buffer.removeAll(keepingCapacity: true)
                    receivingFrame = true
                    escaped = false
                }

                continue
            }

            if escaped {
                buffer.append(byte)
                escaped = false
                continue
            }

            switch byte {
            case Self.escape:
                escaped = true

            case Self.end:
                let frame = buffer
                buffer.removeAll(keepingCapacity: true)
                receivingFrame = false
                escaped = false

                onFrame?(frame)

            case Self.start:
                // Unexpected new frame: restart.
                buffer.removeAll(keepingCapacity: true)
                escaped = false

            default:
                buffer.append(byte)
            }
        }
    }
}
