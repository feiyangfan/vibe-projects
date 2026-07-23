import SwiftUI
import AppKit

struct ContentView: View {

    @EnvironmentObject private var timer: TimerModel
    @EnvironmentObject private var launchAtLogin: LaunchAtLoginManager

    @AppStorage("sitMinutes")
    private var sitMinutes = 30

    @AppStorage("standMinutes")
    private var standMinutes = 15

    @AppStorage("breakMinutes")
    private var breakMinutes = 5
    
    @AppStorage("autoStartNextMode")
    private var autoStartNextMode = true
    
    @AppStorage("notificationsEnabled")
    private var notificationsEnabled = true

    var body: some View {
        VStack(spacing: 16) {
            phaseDisplay

            Divider()

            controls

            Divider()

            durationSettings
            
            Divider()
            
            Toggle("Auto-start next mode", isOn: $autoStartNextMode)

            Text(
                autoStartNextMode
                    ? "The next mode begins automatically."
                    : "A confirmation window appears before the next mode begins."
            )
            .font(.caption)
            .foregroundStyle(.secondary)
            .fixedSize(horizontal: false, vertical: true)

            Divider()
            
            Toggle(
                "Notifications",
                isOn: Binding(
                    get: {
                        notificationsEnabled
                    },
                    set: { enabled in
                        notificationsEnabled = enabled
                        timer.setNotificationsEnabled(enabled)
                    }
                )
            )

            Text(
                notificationsEnabled
                    ? "Show a macOS notification when each mode ends."
                    : "System notifications are disabled."
            )
            .font(.caption)
            .foregroundStyle(.secondary)
            .fixedSize(horizontal: false, vertical: true)
            
            Divider()

            Toggle(
                "Launch at Login",
                isOn: Binding(
                    get: {
                        launchAtLogin.isEnabled
                    },
                    set: { enabled in
                        launchAtLogin.setEnabled(enabled)
                    }
                )
            )

            if let errorMessage = launchAtLogin.errorMessage {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            Divider()

            Button("Quit Stand-Sit Timer") {
                NSApplication.shared.terminate(nil)
            }
            .keyboardShortcut("q")
        }
        .padding(20)
        .frame(width: 300)
    }

    private var phaseDisplay: some View {
        VStack(spacing: 8) {
            Image(systemName: timer.phase.icon)
                .font(.system(size: 28))

            Text(timer.phase.rawValue)
                .font(.headline)

            Text(timer.formattedRemaining)
                .font(.system(size: 36, weight: .semibold, design: .monospaced))
                .monospacedDigit()
        }
    }

    private var controls: some View {
        HStack {
            Button(timer.primaryButtonTitle) {
                timer.toggleTimer()
            }
            .buttonStyle(.borderedProminent)

            Button("Skip") {
                timer.skip()
            }

            Button("Reset") {
                timer.reset()
            }
        }
    }

    private var durationSettings: some View {
        GroupBox("Durations") {
            VStack(alignment: .leading, spacing: 10) {
                Stepper(
                    "Sit: \(sitMinutes) min",
                    value: $sitMinutes,
                    in: 1...180
                )

                Stepper(
                    "Stand: \(standMinutes) min",
                    value: $standMinutes,
                    in: 1...180
                )

                Stepper(
                    "Break: \(breakMinutes) min",
                    value: $breakMinutes,
                    in: 1...60
                )

                Text("Reset the timer to apply a changed duration immediately.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.top, 4)
        }
    }
}
