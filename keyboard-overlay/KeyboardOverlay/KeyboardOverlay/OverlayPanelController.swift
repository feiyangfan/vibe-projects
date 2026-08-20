//
//  OverlayPanelController.swift
//  KeyboardOverlay
//
//  Created by Feiyang Fan on 2026-08-18.
//

import AppKit
import SwiftUI

final class OverlayPanelController {
    private let panel: NSPanel

    let uiState = OverlayUIState()

    private let defaultFrame = NSRect(
        x: 200,
        y: 100,
        width: 900,
        height: 330
    )

    private(set) var isEditing = false

    init(ble: BLETransport) {
        let view = KeyboardOverlayView(
            ble: ble,
            uiState: uiState
        )

        panel = NSPanel(
            contentRect: defaultFrame,
            styleMask: [
                .borderless,
                .nonactivatingPanel,
                .resizable
            ],
            backing: .buffered,
            defer: false
        )

        panel.contentView = NSHostingView(rootView: view)
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = false
        panel.level = .floating

        panel.collectionBehavior = [
            .canJoinAllSpaces,
            .fullScreenAuxiliary
        ]

        panel.minSize = NSSize(
            width: 300,
            height: 110
        )

        panel.isMovableByWindowBackground = true
        panel.setFrameAutosaveName("ZMKOverlayFrame")

        setEditing(false)
    }

    func show() {
        panel.orderFrontRegardless()
    }

    @discardableResult
    func toggleEditing() -> Bool {
        setEditing(!isEditing)
        return isEditing
    }

    func setEditing(_ editing: Bool) {
        isEditing = editing
        uiState.isEditing = editing

        panel.ignoresMouseEvents = !editing
        panel.hasShadow = editing

        if editing {
            panel.makeKeyAndOrderFront(nil)
        } else {
            panel.orderFrontRegardless()
        }
    }

    func resetFrame() {
        panel.setFrame(
            defaultFrame,
            display: true,
            animate: true
        )

        panel.saveFrame(usingName: "ZMKOverlayFrame")
    }
}
