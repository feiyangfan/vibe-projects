import SwiftUI
import AppKit

@main
struct ZMKOverlayApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var overlay: OverlayPanelController?
    var ble: BLETransport?

    private var statusItem: NSStatusItem?
    private var editMenuItem: NSMenuItem?
    private var appearanceWindow: NSWindow?

    func applicationDidFinishLaunching(
        _ notification: Notification
    ) {
        NSApp.setActivationPolicy(.accessory)

        let bleTransport = BLETransport()
        ble = bleTransport

        let overlayController =
            OverlayPanelController(ble: bleTransport)

        overlay = overlayController
        overlayController.show()

        setupStatusMenu()
    }

    private func setupStatusMenu() {
        let item = NSStatusBar.system.statusItem(
            withLength: NSStatusItem.variableLength
        )

        statusItem = item

        if let button = item.button {
            button.image = NSImage(
                systemSymbolName: "keyboard",
                accessibilityDescription: "ZMK Overlay"
            )
            button.toolTip = "ZMK Overlay"
        }

        let menu = NSMenu()

        let editItem = NSMenuItem(
            title: "Edit Overlay",
            action: #selector(toggleOverlayEditing),
            keyEquivalent: ""
        )
        editItem.target = self
        editMenuItem = editItem
        menu.addItem(editItem)

        let appearanceItem = NSMenuItem(
            title: "Appearance…",
            action: #selector(showAppearance),
            keyEquivalent: ","
        )
        appearanceItem.target = self
        menu.addItem(appearanceItem)

        let resetItem = NSMenuItem(
            title: "Reset Overlay Position",
            action: #selector(resetOverlayFrame),
            keyEquivalent: ""
        )
        resetItem.target = self
        menu.addItem(resetItem)

        menu.addItem(.separator())

        let quitItem = NSMenuItem(
            title: "Quit ZMK Overlay",
            action: #selector(quitApp),
            keyEquivalent: "q"
        )
        quitItem.target = self
        menu.addItem(quitItem)

        item.menu = menu
    }

    @objc
    private func toggleOverlayEditing() {
        guard let overlay else {
            return
        }

        let editing = overlay.toggleEditing()

        editMenuItem?.title =
            editing
            ? "Lock Overlay"
            : "Edit Overlay"
    }

    @objc
    private func showAppearance() {
        guard let overlay else {
            return
        }

        if let appearanceWindow {
            appearanceWindow.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        let view = OverlayAppearanceView(
            uiState: overlay.uiState
        )

        let window = NSWindow(
            contentRect: NSRect(
                x: 0,
                y: 0,
                width: 420,
                height: 480
            ),
            styleMask: [
                .titled,
                .closable
            ],
            backing: .buffered,
            defer: false
        )

        window.title = "ZMK Overlay Appearance"
        window.contentView = NSHostingView(rootView: view)
        window.isReleasedWhenClosed = false
        window.center()

        appearanceWindow = window

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    @objc
    private func resetOverlayFrame() {
        overlay?.resetFrame()
    }

    @objc
    private func quitApp() {
        NSApp.terminate(nil)
    }
}
