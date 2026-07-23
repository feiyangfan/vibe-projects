import Foundation
import Combine
import UserNotifications
import AppKit

@MainActor
final class TimerModel: ObservableObject {

    enum Phase: String {
        case sitting = "Sitting"
        case standing = "Standing"
        case breakTime = "Break"

        var next: Phase {
            switch self {
            case .sitting:
                return .standing
            case .standing:
                return .breakTime
            case .breakTime:
                return .sitting
            }
        }

        var shortName: String {
            switch self {
            case .sitting:
                return "Sit"
            case .standing:
                return "Stand"
            case .breakTime:
                return "Break"
            }
        }

        var icon: String {
            switch self {
            case .sitting:
                return "figure.seated.side"
            case .standing:
                return "figure.stand"
            case .breakTime:
                return "cup.and.saucer"
            }
        }

        var notificationTitle: String {
            switch self {
            case .sitting:
                return "Time to sit"
            case .standing:
                return "Time to stand"
            case .breakTime:
                return "Time for a break"
            }
        }

        var instruction: String {
            switch self {
            case .sitting:
                return "Your break is complete. It is time to sit."
            case .standing:
                return "Your sitting period is complete. It is time to stand."
            case .breakTime:
                return "Your standing period is complete. Take a short break."
            }
        }
    }

    @Published private(set) var phase: Phase = .sitting
    @Published private(set) var secondsRemaining: Int
    @Published private(set) var isRunning = false
    @Published private(set) var hasStarted = false
    @Published private(set) var isAwaitingConfirmation = false

    private var endDate: Date?
    private var tickerTask: Task<Void, Never>?

    private let notificationCenter = UNUserNotificationCenter.current()
    private var pendingNotificationID: String?

    private var autoStartNextMode: Bool {
        let defaults = UserDefaults.standard

        // Default to true when the user has not selected a preference yet.
        if defaults.object(forKey: "autoStartNextMode") == nil {
            return true
        }

        return defaults.bool(forKey: "autoStartNextMode")
    }

    init() {
        secondsRemaining = Self.durationSeconds(for: .sitting)
        requestNotificationPermission()
    }

    var formattedRemaining: String {
        let minutes = secondsRemaining / 60
        let seconds = secondsRemaining % 60

        return String(
            format: "%02d:%02d",
            minutes,
            seconds
        )
    }

    var menuTitle: String {
        if isAwaitingConfirmation {
            return "\(phase.next.shortName) ready"
        }

        return "\(phase.shortName) \(formattedRemaining)"
    }

    var primaryButtonTitle: String {
        if isAwaitingConfirmation {
            return "Start \(phase.next.shortName)"
        }

        if isRunning {
            return "Pause"
        }

        return hasStarted ? "Resume" : "Start"
    }

    func toggleTimer() {
        if isAwaitingConfirmation {
            confirmNextMode()
        } else if isRunning {
            pause()
        } else {
            startOrResume()
        }
    }

    func skip() {
        cancelPendingPhaseNotification()

        isAwaitingConfirmation = false
        phase = phase.next
        secondsRemaining = Self.durationSeconds(for: phase)
        hasStarted = true

        if isRunning {
            endDate = Date().addingTimeInterval(
                TimeInterval(secondsRemaining)
            )

            schedulePhaseNotification()
        } else {
            endDate = nil
        }
    }

    func reset() {
        tickerTask?.cancel()
        tickerTask = nil

        cancelPendingPhaseNotification()

        phase = .sitting
        isRunning = false
        hasStarted = false
        isAwaitingConfirmation = false
        endDate = nil
        secondsRemaining = Self.durationSeconds(for: .sitting)
    }

    func confirmNextMode() {
        guard isAwaitingConfirmation else {
            return
        }

        isAwaitingConfirmation = false
        phase = phase.next
        secondsRemaining = Self.durationSeconds(for: phase)
        hasStarted = true
        isRunning = true

        endDate = Date().addingTimeInterval(
            TimeInterval(secondsRemaining)
        )

        startTicker()
        schedulePhaseNotification()
    }

    private func startOrResume() {
        if !hasStarted {
            secondsRemaining = Self.durationSeconds(for: phase)
            hasStarted = true
        }

        if secondsRemaining <= 0 {
            secondsRemaining = Self.durationSeconds(for: phase)
        }

        isAwaitingConfirmation = false
        isRunning = true

        endDate = Date().addingTimeInterval(
            TimeInterval(secondsRemaining)
        )

        startTicker()
        schedulePhaseNotification()
    }

    private func pause() {
        updateRemainingTime()

        isRunning = false
        endDate = nil

        tickerTask?.cancel()
        tickerTask = nil

        cancelPendingPhaseNotification()
    }

    private func startTicker() {
        tickerTask?.cancel()

        tickerTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))

                guard let self, !Task.isCancelled else {
                    return
                }

                self.updateRemainingTime()
            }
        }
    }

    private func updateRemainingTime() {
        guard isRunning, let endDate else {
            return
        }

        secondsRemaining = max(
            0,
            Int(ceil(endDate.timeIntervalSinceNow))
        )

        if secondsRemaining == 0 {
            completeCurrentPhase()
        }
    }

    private func completeCurrentPhase() {
        // The notification for the completed phase is being delivered now.
        // Clear its identifier without cancelling it.
        pendingNotificationID = nil

        if autoStartNextMode {
            startNextModeAutomatically()
        } else {
            waitForNextModeConfirmation()
        }
    }

    private func startNextModeAutomatically() {
        phase = phase.next
        secondsRemaining = Self.durationSeconds(for: phase)
        isRunning = true
        isAwaitingConfirmation = false

        endDate = Date().addingTimeInterval(
            TimeInterval(secondsRemaining)
        )

        schedulePhaseNotification()
    }

    private func waitForNextModeConfirmation() {
        isRunning = false
        isAwaitingConfirmation = true
        endDate = nil
        secondsRemaining = 0

        tickerTask?.cancel()
        tickerTask = nil

        let nextPhase = phase.next

        showTransitionAlert(for: nextPhase)
    }

    private func showTransitionAlert(for nextPhase: Phase) {
        NSApplication.shared.activate(ignoringOtherApps: true)

        let alert = NSAlert()
        alert.alertStyle = .informational
        alert.messageText = nextPhase.notificationTitle
        alert.informativeText = nextPhase.instruction
        alert.icon = NSImage(
            systemSymbolName: nextPhase.icon,
            accessibilityDescription: nextPhase.rawValue
        )

        alert.addButton(
            withTitle: "Start \(nextPhase.shortName)"
        )

        alert.addButton(
            withTitle: "Later"
        )

        let response = alert.runModal()

        if response == .alertFirstButtonReturn {
            confirmNextMode()
        }
    }

    private func requestNotificationPermission() {
        notificationCenter.getNotificationSettings { [weak self] settings in
            guard let self else {
                return
            }

            guard settings.authorizationStatus == .notDetermined else {
                return
            }

            self.notificationCenter.requestAuthorization(
                options: [.alert, .sound]
            ) { granted, error in
                if let error {
                    print(
                        "Notification authorization error:",
                        error.localizedDescription
                    )
                    return
                }

                print(
                    granted
                        ? "Notification permission granted."
                        : "Notification permission declined."
                )
            }
        }
    }
    
    private var notificationsEnabled: Bool {
        let defaults = UserDefaults.standard

        if defaults.object(forKey: "notificationsEnabled") == nil {
            return true
        }

        return defaults.bool(forKey: "notificationsEnabled")
    }
    
    func setNotificationsEnabled(_ enabled: Bool) {
        UserDefaults.standard.set(
            enabled,
            forKey: "notificationsEnabled"
        )

        if enabled {
            if isRunning {
                schedulePhaseNotification()
            }
        } else {
            cancelPendingPhaseNotification()
        }
    }

    private func schedulePhaseNotification() {
        cancelPendingPhaseNotification()

        guard notificationsEnabled else {
            return
        }

        let currentPhase = phase
        let nextPhase = phase.next
        let delay = TimeInterval(max(1, secondsRemaining))

        notificationCenter.getNotificationSettings { [weak self] settings in
            guard let self else {
                return
            }

            guard settings.authorizationStatus == .authorized ||
                    settings.authorizationStatus == .provisional else {
                print(
                    "Notification not scheduled because permission is not enabled."
                )
                return
            }

            let notificationID = UUID().uuidString

            let content = UNMutableNotificationContent()
            content.title = nextPhase.notificationTitle
            content.body = "\(currentPhase.rawValue) time is complete."
            content.sound = .default

            let trigger = UNTimeIntervalNotificationTrigger(
                timeInterval: delay,
                repeats: false
            )

            let request = UNNotificationRequest(
                identifier: notificationID,
                content: content,
                trigger: trigger
            )

            self.notificationCenter.add(request) { error in
                if let error {
                    print(
                        "Notification scheduling error:",
                        error.localizedDescription
                    )
                    return
                }

                Task { @MainActor [weak self] in
                    self?.pendingNotificationID = notificationID
                }
            }
        }
    }

    private func cancelPendingPhaseNotification() {
        guard let pendingNotificationID else {
            return
        }

        notificationCenter.removePendingNotificationRequests(
            withIdentifiers: [pendingNotificationID]
        )

        self.pendingNotificationID = nil
    }

    private static func durationSeconds(for phase: Phase) -> Int {
        let defaults = UserDefaults.standard

        let key: String
        let fallbackMinutes: Int

        switch phase {
        case .sitting:
            key = "sitMinutes"
            fallbackMinutes = 45

        case .standing:
            key = "standMinutes"
            fallbackMinutes = 15

        case .breakTime:
            key = "breakMinutes"
            fallbackMinutes = 5
        }

        let savedMinutes =
            defaults.object(forKey: key) as? Int
            ?? fallbackMinutes

        return max(1, savedMinutes) * 60
    }
}
