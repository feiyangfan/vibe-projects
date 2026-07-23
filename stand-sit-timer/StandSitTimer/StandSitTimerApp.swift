import SwiftUI
import UserNotifications

@main
struct StandSitTimerApp: App {
    @StateObject private var timer = TimerModel()
    @StateObject private var launchAtLogin = LaunchAtLoginManager()

    private let notificationDelegate: NotificationDelegate

    init() {
        let delegate = NotificationDelegate()
        notificationDelegate = delegate

        UNUserNotificationCenter.current().delegate = delegate
    }

    var body: some Scene {
        MenuBarExtra {
            ContentView()
                .environmentObject(timer)
                .environmentObject(launchAtLogin)
        } label: {
            HStack(spacing: 5) {
                Image(
                    systemName: timer.isRunning
                        ? timer.phase.icon
                        : "pause.fill"
                )

                Text(
                    "\(timer.phase.shortName) \(timer.formattedRemaining)"
                )
                .monospacedDigit()
            }
        }
        .menuBarExtraStyle(.window)
    }
}
