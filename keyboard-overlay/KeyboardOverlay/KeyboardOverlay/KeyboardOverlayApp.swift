import SwiftUI
import AppKit
import Combine

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
    var practice: PracticeState?
    var usage: UsageAnalyticsState?

    private var statusItem: NSStatusItem?
    private var editMenuItem: NSMenuItem?
    private var heatmapMenuItem: NSMenuItem?
    private var refreshMenuItem: NSMenuItem?
    private var appearanceWindow: NSWindow?
    private var practiceWindow: NSWindow?
    private var usageWindow: NSWindow?
    private var appCancellables = Set<AnyCancellable>()

    func applicationDidFinishLaunching(
        _ notification: Notification
    ) {
        NSApp.setActivationPolicy(.accessory)

        let bleTransport = BLETransport()
        ble = bleTransport

        let practiceState = PracticeState(
            ble: bleTransport
        )
        practice = practiceState

        let usageState = UsageAnalyticsState(
            ble: bleTransport,
            practice: practiceState
        )
        usage = usageState

        // Smart Practice combines persistent mastery with passive real-world
        // usage. Attach after both objects exist to avoid a retain/init cycle.
        practiceState.attachUsage(
            usageState
        )

        let overlayController =
            OverlayPanelController(
                ble: bleTransport,
                practice: practiceState,
                usage: usageState
            )

        overlay = overlayController
        overlayController.show()

        setupStatusMenu()
        observeRefreshState(
            bleTransport
        )
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

        let practiceItem = NSMenuItem(
            title: "Practice Keymap…",
            action: #selector(showPractice),
            keyEquivalent: "p"
        )
        practiceItem.target = self
        menu.addItem(practiceItem)

        let usageItem = NSMenuItem(
            title: "Usage Statistics…",
            action: #selector(showUsageStatistics),
            keyEquivalent: "u"
        )
        usageItem.target = self
        menu.addItem(usageItem)

        let heatmapItem = NSMenuItem(
            title: "Show Usage Heatmap",
            action: #selector(toggleUsageHeatmap),
            keyEquivalent: ""
        )
        heatmapItem.target = self
        heatmapItem.state =
            usage?.showHeatmap == true
            ? .on
            : .off
        heatmapMenuItem = heatmapItem
        menu.addItem(heatmapItem)

        let refreshItem = NSMenuItem(
            title: "Refresh Keymap",
            action: #selector(refreshKeymap),
            keyEquivalent: "r"
        )
        refreshItem.target = self
        refreshMenuItem = refreshItem
        menu.addItem(refreshItem)

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

    private func observeRefreshState(
        _ ble: BLETransport
    ) {
        ble.$isRefreshingKeymap
            .receive(on: DispatchQueue.main)
            .sink { [weak self] refreshing in
                guard let self else {
                    return
                }

                self.refreshMenuItem?.title =
                    refreshing
                    ? "Refreshing Keymap…"
                    : "Refresh Keymap"

                self.refreshMenuItem?.isEnabled =
                    !refreshing
            }
            .store(
                in: &appCancellables
            )
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
    private func showPractice() {
        guard
            let ble,
            let practice
        else {
            return
        }

        if let practiceWindow {
            practiceWindow.makeKeyAndOrderFront(nil)
            NSApp.activate(
                ignoringOtherApps: true
            )
            return
        }

        let view = PracticeModeView(
            ble: ble,
            practice: practice
        )

        let window = NSWindow(
            contentRect: NSRect(
                x: 0,
                y: 0,
                width: 520,
                height: 610
            ),
            styleMask: [
                .titled,
                .closable,
                .miniaturizable
            ],
            backing: .buffered,
            defer: false
        )

        window.title = "ZMK Overlay Practice"
        window.contentView =
            NSHostingView(rootView: view)
        window.isReleasedWhenClosed = false
        window.center()

        practiceWindow = window

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(
            ignoringOtherApps: true
        )
    }

    @objc
    private func showUsageStatistics() {
        guard
            let ble,
            let usage
        else {
            return
        }

        if let usageWindow {
            usageWindow.makeKeyAndOrderFront(nil)
            NSApp.activate(
                ignoringOtherApps: true
            )
            return
        }

        let view = UsageStatisticsView(
            ble: ble,
            usage: usage
        )

        let window = NSWindow(
            contentRect: NSRect(
                x: 0,
                y: 0,
                width: 560,
                height: 560
            ),
            styleMask: [
                .titled,
                .closable,
                .miniaturizable,
                .resizable
            ],
            backing: .buffered,
            defer: false
        )

        window.title = "ZMK Overlay Usage Statistics"
        window.contentView =
            NSHostingView(rootView: view)
        window.isReleasedWhenClosed = false
        window.center()

        usageWindow = window

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(
            ignoringOtherApps: true
        )
    }

    @objc
    private func toggleUsageHeatmap() {
        guard let usage else {
            return
        }

        usage.showHeatmap.toggle()

        heatmapMenuItem?.state =
            usage.showHeatmap
            ? .on
            : .off
    }

    @objc
    private func refreshKeymap() {
        guard
            let ble,
            !ble.isRefreshingKeymap
        else {
            return
        }

        if !ble.refreshKeymap() {
            NSSound.beep()
        }
    }

    @objc
    private func resetOverlayFrame() {
        overlay?.resetFrame()
    }

    func applicationWillTerminate(
        _ notification: Notification
    ) {
        usage?.flushCurrentDwell()
    }

    @objc
    private func quitApp() {
        usage?.flushCurrentDwell()
        NSApp.terminate(nil)
    }
}

// MARK: - Practice Mode

final class PracticeState: ObservableObject {

    enum PracticeStyle: String, CaseIterable, Identifiable {
        case smart
        case weakKeys
        case random

        var id: String {
            rawValue
        }

        var title: String {
            switch self {
            case .smart:
                return "Smart"

            case .weakKeys:
                return "Weak Keys"

            case .random:
                return "Random"
            }
        }

        var detail: String {
            switch self {
            case .smart:
                return "Mastery + real usage"

            case .weakKeys:
                return "Mastery only"

            case .random:
                return "Equal distribution"
            }
        }
    }

    struct MasteryRecord: Codable {
        var attempts = 0
        var correct = 0
        var totalCorrectResponseTime: Double = 0
        var lastPracticed: Date?

        var accuracy: Double {
            guard attempts > 0 else {
                return 0
            }

            return Double(correct) /
                Double(attempts)
        }

        var averageCorrectResponseTime: Double? {
            guard correct > 0 else {
                return nil
            }

            return totalCorrectResponseTime /
                Double(correct)
        }
    }

    private struct Candidate {
        let position: Int
        let label: String
    }

    @Published var isActive = false
    @Published var selectedLayerIndex = 0

    @Published private(set) var targetPosition: Int?
    @Published private(set) var targetLabel = ""

    @Published var hideOverlayLabels = false
    @Published var showTargetHint = true

    @Published var practiceStyle: PracticeStyle {
        didSet {
            defaults.set(
                practiceStyle.rawValue,
                forKey: practiceStyleDefaultsKey
            )

            if isActive {
                chooseNextTarget()
            }
        }
    }

    @Published private(set) var correctCount = 0
    @Published private(set) var wrongCount = 0
    @Published private(set) var lastResult = ""

    @Published private(set) var sessionCorrectResponseTime: Double = 0

    private weak var ble: BLETransport?
    private weak var usage: UsageAnalyticsState?

    private var previousPressedKeys: Set<Int> = []
    private var cancellables = Set<AnyCancellable>()
    private var targetGeneration = 0
    private var targetStartedAt: Date?

    private var masteryByKey: [String: MasteryRecord] = [:]

    private let defaults = UserDefaults.standard
    private let masteryDefaultsKey = "Practice.mastery.v1"
    private let practiceStyleDefaultsKey =
        "Practice.style.v1"

    init(ble: BLETransport) {
        let storedStyle =
            UserDefaults.standard.string(
                forKey: "Practice.style.v1"
            )

        practiceStyle =
            PracticeStyle(
                rawValue:
                    storedStyle ?? ""
            )
            ?? .smart

        self.ble = ble

        loadMastery()

        previousPressedKeys = ble.pressedKeys

        ble.$pressedKeys
            .receive(on: DispatchQueue.main)
            .sink { [weak self] pressedKeys in
                self?.handlePressedKeys(pressedKeys)
            }
            .store(in: &cancellables)

        ble.$layerNames
            .receive(on: DispatchQueue.main)
            .sink { [weak self] names in
                guard let self else { return }

                if names.isEmpty {
                    self.stop()
                    self.selectedLayerIndex = 0
                    return
                }

                if self.selectedLayerIndex >= names.count {
                    self.selectedLayerIndex = 0
                }

                // Refreshing the keymap can change both the layer list and
                // the candidate positions. Re-select from the new cache.
                if self.isActive {
                    self.chooseNextTarget()
                }
            }
            .store(in: &cancellables)
    }

    func attachUsage(
        _ usage: UsageAnalyticsState
    ) {
        self.usage = usage

        usage.$keyRecords
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                self?.objectWillChange.send()
            }
            .store(in: &cancellables)

        if isActive &&
           practiceStyle == .smart {
            chooseNextTarget()
        }
    }


    // MARK: - Session summary

    var selectedLayerName: String {
        guard
            let ble,
            selectedLayerIndex >= 0,
            selectedLayerIndex < ble.layerNames.count
        else {
            return "Layer"
        }

        return ble.layerNames[selectedLayerIndex]
    }

    var totalAttempts: Int {
        correctCount + wrongCount
    }

    var accuracyText: String {
        guard totalAttempts > 0 else {
            return "—"
        }

        let accuracy =
            Double(correctCount) /
            Double(totalAttempts) * 100.0

        return String(
            format: "%.0f%%",
            accuracy
        )
    }

    var averageResponseTimeText: String {
        guard correctCount > 0 else {
            return "—"
        }

        let average =
            sessionCorrectResponseTime /
            Double(correctCount)

        return String(
            format: "%.2fs",
            average
        )
    }

    var currentTargetHistoryText: String {
        guard
            let ble,
            let position = targetPosition
        else {
            return "New key"
        }

        let key = masteryKey(
            layerIndex: selectedLayerIndex,
            position: position,
            label: targetLabel,
            ble: ble
        )

        guard
            let record = masteryByKey[key],
            record.attempts > 0
        else {
            return "New key"
        }

        let accuracy =
            String(
                format: "%.0f%%",
                record.accuracy * 100.0
            )

        if let average =
            record.averageCorrectResponseTime {
            return
                "\(accuracy) • \(String(format: "%.2fs", average)) • \(record.attempts) tries"
        }

        return
            "\(accuracy) • \(record.attempts) tries"
    }

    var weakestKeysText: String {
        guard let ble else {
            return "—"
        }

        let candidates = practiceCandidates(
            layerIndex: selectedLayerIndex,
            ble: ble
        )

        let scored = candidates.map {
            candidate in

            (
                label: candidate.label,
                score: weaknessScore(
                    candidate,
                    layerIndex:
                        selectedLayerIndex,
                    ble: ble
                )
            )
        }
        .sorted {
            $0.score > $1.score
        }

        let labels =
            scored.prefix(3).map(\.label)

        return labels.isEmpty
            ? "—"
            : labels.joined(separator: ", ")
    }

    var recommendedKeysText: String {
        if practiceStyle == .random {
            return "All keys equal"
        }

        guard let ble else {
            return "—"
        }

        let candidates = practiceCandidates(
            layerIndex:
                selectedLayerIndex,
            ble: ble
        )

        let ranked =
            candidates.map {
                candidate in

                (
                    label: candidate.label,
                    priority:
                        targetWeight(
                            candidate,
                            layerIndex:
                                selectedLayerIndex,
                            ble: ble
                        )
                )
            }
            .sorted {
                $0.priority >
                    $1.priority
            }

        let labels =
            ranked.prefix(3)
                .map(\.label)

        return labels.isEmpty
            ? "—"
            : labels.joined(
                separator: ", "
            )
    }

    var practiceStyleDetail: String {
        practiceStyle.detail
    }


    // MARK: - Session lifecycle

    func start() {
        guard
            let ble,
            selectedLayerIndex >= 0,
            selectedLayerIndex < ble.layerLabels.count,
            !practiceCandidates(
                layerIndex: selectedLayerIndex,
                ble: ble
            ).isEmpty
        else {
            lastResult =
                "No practiceable keys on this layer"
            isActive = false
            return
        }

        correctCount = 0
        wrongCount = 0
        sessionCorrectResponseTime = 0
        lastResult = ""

        previousPressedKeys = ble.pressedKeys

        isActive = true
        chooseNextTarget()
    }

    func stop() {
        targetGeneration += 1
        isActive = false
        targetPosition = nil
        targetLabel = ""
        targetStartedAt = nil
        lastResult = ""
    }

    func resetSessionStats() {
        correctCount = 0
        wrongCount = 0
        sessionCorrectResponseTime = 0
        lastResult = ""
    }

    func resetMasteryForSelectedLayer() {
        guard let ble else {
            return
        }

        let prefix =
            "\(ble.practiceStorageIdentifier)|" +
            "\(selectedLayerID(in: ble))|"

        masteryByKey =
            masteryByKey.filter {
                !$0.key.hasPrefix(prefix)
            }

        saveMastery()

        lastResult =
            "Learning history reset for \(selectedLayerName)"

        if isActive {
            chooseNextTarget()
        }
    }


    // MARK: - Adaptive target selection

    func chooseNextTarget() {
        guard
            isActive,
            let ble
        else {
            return
        }

        let candidates = practiceCandidates(
            layerIndex: selectedLayerIndex,
            ble: ble
        )

        guard !candidates.isEmpty else {
            stop()
            lastResult =
                "No practiceable keys on this layer"
            return
        }

        let previousTarget = targetPosition

        let choices: [Candidate]

        if candidates.count > 1,
           let previousTarget {
            choices = candidates.filter {
                $0.position != previousTarget
            }
        } else {
            choices = candidates
        }

        guard
            let target = weightedTarget(
                from: choices,
                layerIndex: selectedLayerIndex,
                ble: ble
            )
        else {
            return
        }

        targetGeneration += 1
        targetPosition = target.position
        targetLabel = target.label
        targetStartedAt = Date()
    }

    private func weightedTarget(
        from candidates: [Candidate],
        layerIndex: Int,
        ble: BLETransport
    ) -> Candidate? {
        guard !candidates.isEmpty else {
            return nil
        }

        let weighted =
            candidates.map {
                candidate in

                (
                    candidate: candidate,
                    weight: targetWeight(
                        candidate,
                        layerIndex:
                            layerIndex,
                        ble: ble
                    )
                )
            }

        let totalWeight =
            weighted.reduce(0.0) {
                $0 + $1.weight
            }

        guard totalWeight > 0 else {
            return candidates.randomElement()
        }

        var selection =
            Double.random(
                in: 0..<totalWeight
            )

        for item in weighted {
            selection -= item.weight

            if selection <= 0 {
                return item.candidate
            }
        }

        return weighted.last?.candidate
    }

    private func targetWeight(
        _ candidate: Candidate,
        layerIndex: Int,
        ble: BLETransport
    ) -> Double {
        switch practiceStyle {
        case .smart:
            return smartWeight(
                candidate,
                layerIndex:
                    layerIndex,
                ble: ble
            )

        case .weakKeys:
            return adaptiveWeight(
                candidate,
                layerIndex:
                    layerIndex,
                ble: ble
            )

        case .random:
            return 1.0
        }
    }

    /*
     * Smart Practice starts with the existing mastery/recall weight and
     * multiplies it by real-world importance. Usage is normalized inside the
     * selected layer so frequently used weak keys are prioritized, while
     * rarely used keys still retain a meaningful review floor.
     */
    private func smartWeight(
        _ candidate: Candidate,
        layerIndex: Int,
        ble: BLETransport
    ) -> Double {
        let masteryWeight =
            adaptiveWeight(
                candidate,
                layerIndex:
                    layerIndex,
                ble: ble
            )

        guard let usage else {
            // Usage data may not be attached during very early startup.
            return masteryWeight
        }

        let usageLevel =
            usage.usageImportance(
                for: layerIndex,
                position:
                    candidate.position,
                label:
                    candidate.label
            )

        /*
         * Multiplier range: 0.75 ... 2.25.
         *
         * Even a never-used key keeps 75% of its mastery weight, preventing
         * uncommon keys from disappearing from training. A heavily used key
         * can receive up to 3x the priority of a zero-use key with otherwise
         * identical mastery.
         */
        let usageMultiplier =
            0.75 +
            1.50 * usageLevel

        return max(
            0.20,
            masteryWeight *
                usageMultiplier
        )
    }


    /*
     * New, inaccurate, slow, and long-unseen keys receive larger weights.
     * Well-known fast keys remain in rotation, but much less frequently.
     */
    private func adaptiveWeight(
        _ candidate: Candidate,
        layerIndex: Int,
        ble: BLETransport
    ) -> Double {
        let key = masteryKey(
            layerIndex: layerIndex,
            position: candidate.position,
            label: candidate.label,
            ble: ble
        )

        guard
            let record = masteryByKey[key],
            record.attempts > 0
        else {
            return 5.0
        }

        var weight = 0.55

        // Incorrect history is the strongest signal.
        weight +=
            (1.0 - record.accuracy) * 4.0

        // Give under-practiced keys extra exposure.
        if record.attempts < 3 {
            weight +=
                Double(3 - record.attempts) * 0.8
        }

        // Slow successful recall should continue appearing.
        if let average =
            record.averageCorrectResponseTime {
            let slowBonus =
                max(
                    0,
                    min(
                        2.0,
                        (average - 0.9) / 1.2
                    )
                )

            weight += slowBonus
        } else {
            weight += 1.0
        }

        // Bring older knowledge back into rotation.
        if let lastPracticed =
            record.lastPracticed {
            let ageDays =
                Date().timeIntervalSince(
                    lastPracticed
                ) / 86_400.0

            weight +=
                max(
                    0,
                    min(
                        1.5,
                        ageDays / 7.0
                    )
                )
        }

        return max(0.25, weight)
    }

    private func weaknessScore(
        _ candidate: Candidate,
        layerIndex: Int,
        ble: BLETransport
    ) -> Double {
        adaptiveWeight(
            candidate,
            layerIndex: layerIndex,
            ble: ble
        )
    }


    // MARK: - Live key verification

    private func handlePressedKeys(
        _ pressedKeys: Set<Int>
    ) {
        defer {
            previousPressedKeys = pressedKeys
        }

        guard
            isActive,
            let ble,
            let targetPosition
        else {
            return
        }

        let newlyPressed =
            pressedKeys.subtracting(
                previousPressedKeys
            )

        guard !newlyPressed.isEmpty else {
            return
        }

        /*
         * Layer activation itself is not a quiz attempt. Only score physical
         * presses after Companion F21 reports that the requested layer is
         * actually active.
         */
        guard
            ble.activeLayer ==
                selectedLayerIndex
        else {
            return
        }

        for position in newlyPressed.sorted() {
            if position == targetPosition {
                let responseTime =
                    targetStartedAt.map {
                        Date().timeIntervalSince($0)
                    }

                correctCount += 1

                if let responseTime {
                    sessionCorrectResponseTime +=
                        responseTime
                }

                recordAttempt(
                    position: targetPosition,
                    label: targetLabel,
                    correct: true,
                    responseTime: responseTime,
                    ble: ble
                )

                if let responseTime {
                    lastResult =
                        String(
                            format:
                                "Correct ✓  %.2fs",
                            responseTime
                        )
                } else {
                    lastResult = "Correct ✓"
                }

                let completedGeneration =
                    targetGeneration

                DispatchQueue.main.asyncAfter(
                    deadline: .now() + 0.45
                ) { [weak self] in
                    guard
                        let self,
                        self.isActive,
                        self.targetGeneration ==
                            completedGeneration
                    else {
                        return
                    }

                    self.lastResult = ""
                    self.chooseNextTarget()
                }

                return
            }

            wrongCount += 1

            recordAttempt(
                position: targetPosition,
                label: targetLabel,
                correct: false,
                responseTime: nil,
                ble: ble
            )

            let actualLabel =
                label(
                    for: position,
                    layerIndex:
                        selectedLayerIndex,
                    ble: ble
                )

            if actualLabel.isEmpty {
                lastResult = "Wrong key"
            } else {
                lastResult =
                    "Wrong — \(actualLabel)"
            }

            /*
             * Keep the same target after a mistake. This reinforces immediate
             * correction instead of allowing a wrong press to skip the item.
             */
            return
        }
    }


    // MARK: - Dynamic candidate generation

    private func practiceCandidates(
        layerIndex: Int,
        ble: BLETransport
    ) -> [Candidate] {
        guard
            layerIndex >= 0,
            layerIndex < ble.layerLabels.count
        else {
            return []
        }

        let labels =
            ble.layerLabels[layerIndex]

        let physicalPositions =
            Set(ble.physicalKeys.map(\.id))

        let layerOnlyLabels =
            Set(ble.layerNames)

        let rawCandidates =
            labels.enumerated().compactMap {
                position,
                rawLabel -> Candidate? in

                let label =
                    rawLabel.trimmingCharacters(
                        in: .whitespacesAndNewlines
                    )

                guard
                    physicalPositions.contains(
                        position
                    ),
                    !label.isEmpty,
                    label != "Unknown",
                    label != "Transparent",
                    !layerOnlyLabels.contains(label)
                else {
                    return nil
                }

                return Candidate(
                    position: position,
                    label: label
                )
            }

        /*
         * The prompt shows a key label, not a position number. Exclude labels
         * that exist at multiple positions on the same layer so hard mode
         * never asks an ambiguous "find X" question.
         */
        let counts =
            Dictionary(
                grouping:
                    rawCandidates,
                by: \.label
            )
            .mapValues(\.count)

        return rawCandidates.filter {
            counts[$0.label] == 1
        }
    }

    private func label(
        for position: Int,
        layerIndex: Int,
        ble: BLETransport
    ) -> String {
        guard
            layerIndex >= 0,
            layerIndex <
                ble.layerLabels.count,
            position >= 0,
            position <
                ble.layerLabels[layerIndex].count
        else {
            return ""
        }

        return
            ble.layerLabels[layerIndex][position]
    }


    // MARK: - Persistent mastery

    private func selectedLayerID(
        in ble: BLETransport
    ) -> Int {
        guard
            selectedLayerIndex >= 0,
            selectedLayerIndex < ble.layerIDs.count
        else {
            return selectedLayerIndex
        }

        return ble.layerIDs[selectedLayerIndex]
    }

    private func masteryKey(
        layerIndex: Int,
        position: Int,
        label: String,
        ble: BLETransport
    ) -> String {
        let layerID: Int

        if layerIndex >= 0,
           layerIndex < ble.layerIDs.count {
            layerID = ble.layerIDs[layerIndex]
        } else {
            layerID = layerIndex
        }

        return [
            ble.practiceStorageIdentifier,
            String(layerID),
            String(position),
            label
        ]
        .joined(separator: "|")
    }

    private func recordAttempt(
        position: Int,
        label: String,
        correct: Bool,
        responseTime: Double?,
        ble: BLETransport
    ) {
        let key = masteryKey(
            layerIndex:
                selectedLayerIndex,
            position: position,
            label: label,
            ble: ble
        )

        var record =
            masteryByKey[key]
            ?? MasteryRecord()

        record.attempts += 1

        if correct {
            record.correct += 1

            if let responseTime {
                record.totalCorrectResponseTime +=
                    responseTime
            }
        }

        record.lastPracticed = Date()

        masteryByKey[key] = record
        saveMastery()
    }

    private func loadMastery() {
        guard
            let data =
                defaults.data(
                    forKey:
                        masteryDefaultsKey
                )
        else {
            return
        }

        do {
            masteryByKey =
                try JSONDecoder().decode(
                    [String: MasteryRecord].self,
                    from: data
                )
        } catch {
            print(
                "Failed to load practice mastery:",
                error
            )
        }
    }

    private func saveMastery() {
        do {
            let data =
                try JSONEncoder().encode(
                    masteryByKey
                )

            defaults.set(
                data,
                forKey:
                    masteryDefaultsKey
            )
        } catch {
            print(
                "Failed to save practice mastery:",
                error
            )
        }
    }
}


struct PracticeModeView: View {
    @ObservedObject var ble: BLETransport
    @ObservedObject var practice: PracticeState

    var body: some View {
        VStack(
            alignment: .leading,
            spacing: 14
        ) {
            HStack {
                Text("Practice Keymap")
                    .font(.title2.bold())

                Spacer()

                Text(
                    ble.hasCachedOverlay
                    ? "Cached keymap"
                    : "No cached keymap"
                )
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            Divider()

            HStack {
                Text("Layer")

                Picker(
                    "Layer",
                    selection:
                        $practice.selectedLayerIndex
                ) {
                    ForEach(
                        Array(
                            ble.layerNames.enumerated()
                        ),
                        id: \.offset
                    ) { index, name in
                        Text(name)
                            .tag(index)
                    }
                }
                .labelsHidden()
                .frame(maxWidth: 220)

                Spacer()

                if practice.isActive {
                    Button("Stop") {
                        practice.stop()
                    }
                } else {
                    Button("Start") {
                        practice.start()
                    }
                    .keyboardShortcut(
                        .defaultAction
                    )
                    .disabled(
                        ble.layerNames.isEmpty
                    )
                }
            }

            HStack {
                Text("Practice Style")

                Picker(
                    "Practice Style",
                    selection:
                        $practice.practiceStyle
                ) {
                    ForEach(
                        PracticeState.PracticeStyle
                            .allCases
                    ) { style in
                        Text(style.title)
                            .tag(style)
                    }
                }
                .labelsHidden()
                .pickerStyle(.segmented)
                .frame(maxWidth: 300)

                Spacer()

                Text(
                    practice.practiceStyleDetail
                )
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            GroupBox {
                VStack(spacing: 7) {
                    if practice.isActive {
                        Text(
                            ble.activeLayer ==
                                practice.selectedLayerIndex
                            ? "Press"
                            : "Activate \(practice.selectedLayerName), then press"
                        )
                        .font(.callout)
                        .foregroundStyle(.secondary)

                        Text(
                            practice.targetLabel
                        )
                        .font(
                            .system(
                                size: 36,
                                weight: .bold,
                                design: .rounded
                            )
                        )
                        .minimumScaleFactor(0.5)
                        .lineLimit(2)
                        .frame(
                            maxWidth: .infinity,
                            minHeight: 50
                        )

                        Text(
                            practice.currentTargetHistoryText
                        )
                        .font(.caption)
                        .foregroundStyle(.secondary)

                        Text(
                            practice.lastResult.isEmpty
                            ? " "
                            : practice.lastResult
                        )
                        .font(.headline)
                        .foregroundStyle(
                            practice.lastResult
                                .hasPrefix("Correct")
                            ? Color.green
                            : Color.secondary
                        )
                    } else {
                        Text(
                            ble.layerNames.isEmpty
                            ? "Refresh the keymap first."
                            : "Choose a layer and style. Smart Practice combines real-world usage with mastery, recall speed, and review age."
                        )
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .frame(
                            maxWidth: .infinity,
                            minHeight: 100
                        )
                    }
                }
                .padding(8)
            }

            HStack(spacing: 20) {
                stat(
                    title: "Correct",
                    value:
                        "\(practice.correctCount)"
                )

                stat(
                    title: "Wrong",
                    value:
                        "\(practice.wrongCount)"
                )

                stat(
                    title: "Accuracy",
                    value:
                        practice.accuracyText
                )

                stat(
                    title: "Avg time",
                    value:
                        practice.averageResponseTimeText
                )

                Spacer()
            }

            HStack {
                VStack(
                    alignment: .leading,
                    spacing: 2
                ) {
                    Text("Needs practice")
                        .font(.caption)
                        .foregroundStyle(
                            .secondary
                        )

                    Text(
                        practice.weakestKeysText
                    )
                    .font(.callout)
                    .lineLimit(1)
                }

                Spacer()

                Button("Reset Session") {
                    practice.resetSessionStats()
                }
                .disabled(
                    practice.totalAttempts == 0
                )

                Button("Reset Layer Learning") {
                    practice.resetMasteryForSelectedLayer()
                }
            }

            HStack {
                VStack(
                    alignment: .leading,
                    spacing: 2
                ) {
                    Text("Recommended now")
                        .font(.caption)
                        .foregroundStyle(
                            .secondary
                        )

                    Text(
                        practice.recommendedKeysText
                    )
                    .font(.callout)
                    .lineLimit(1)
                }

                Spacer()

                Text(
                    practice.practiceStyle.title
                )
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            Divider()

            Toggle(
                "Hide overlay key labels",
                isOn:
                    $practice.hideOverlayLabels
            )

            Toggle(
                "Highlight target position",
                isOn:
                    $practice.showTargetHint
            )

            Text(
                "Learning history is saved locally. After Refresh Keymap, moved or changed bindings automatically start fresh because mastery is tied to the keyboard, layer, physical position, and current label."
            )
            .font(.caption)
            .foregroundStyle(.secondary)

            Spacer()
        }
        .padding(18)
        .frame(
            width: 520,
            height: 610
        )
        .onChange(
            of: practice.selectedLayerIndex
        ) { _ in
            if practice.isActive {
                practice.start()
            }
        }
    }

    private func stat(
        title: String,
        value: String
    ) -> some View {
        VStack(
            alignment: .leading,
            spacing: 2
        ) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)

            Text(value)
                .font(
                    .system(
                        .title3,
                        design: .monospaced
                    )
                )
        }
    }
}

// MARK: - Passive Usage Analytics

final class UsageAnalyticsState: ObservableObject {

    struct LayerUsageRecord: Codable {
        var activations = 0
        var dwellSeconds: Double = 0
        var latestName = ""
    }

    struct KeyUsageRecord: Codable {
        var count = 0
        var latestLabel = ""
    }

    struct KeyUsageSummary: Identifiable {
        let position: Int
        let label: String
        let count: Int

        var id: String {
            "\(position)|\(label)"
        }
    }

    @Published private(set)
    var layerRecords: [String: LayerUsageRecord] = [:]

    @Published private(set)
    var keyRecords: [String: KeyUsageRecord] = [:]

    @Published var showHeatmap: Bool {
        didSet {
            defaults.set(
                showHeatmap,
                forKey: heatmapDefaultsKey
            )
        }
    }

    private weak var ble: BLETransport?
    private weak var practice: PracticeState?

    private var previousPressedKeys: Set<Int> = []
    private var trackedLayerIndex: Int?
    private var dwellStartedAt: Date?
    private var runtimeReady = false
    private var practiceActive = false

    private var cancellables = Set<AnyCancellable>()
    private var saveWorkItem: DispatchWorkItem?

    private let defaults = UserDefaults.standard
    private let heatmapDefaultsKey =
        "UsageAnalytics.showHeatmap"
    private let layerDefaultsKey =
        "UsageAnalytics.layers.v1"
    private let keyDefaultsKey =
        "UsageAnalytics.keys.v1"

    init(
        ble: BLETransport,
        practice: PracticeState
    ) {
        showHeatmap =
            UserDefaults.standard.object(
                forKey: "UsageAnalytics.showHeatmap"
            ) as? Bool
            ?? false

        self.ble = ble
        self.practice = practice

        load()

        previousPressedKeys = ble.pressedKeys
        runtimeReady = ble.companionRuntimeReady
        practiceActive = practice.isActive

        ble.$pressedKeys
            .receive(on: DispatchQueue.main)
            .sink { [weak self] keys in
                self?.handlePressedKeys(keys)
            }
            .store(in: &cancellables)

        ble.$activeLayer
            .removeDuplicates()
            .receive(on: DispatchQueue.main)
            .sink { [weak self] index in
                self?.handleLayerChange(index)
            }
            .store(in: &cancellables)

        ble.$companionRuntimeReady
            .removeDuplicates()
            .receive(on: DispatchQueue.main)
            .sink { [weak self] ready in
                self?.handleRuntimeReady(ready)
            }
            .store(in: &cancellables)

        practice.$isActive
            .removeDuplicates()
            .receive(on: DispatchQueue.main)
            .sink { [weak self] active in
                self?.handlePracticeActive(active)
            }
            .store(in: &cancellables)
    }


    // MARK: - Public statistics

    var totalKeyPresses: Int {
        currentKeyboardKeyRecords()
            .values
            .reduce(0) {
                $0 + $1.count
            }
    }

    func activations(
        for layerIndex: Int
    ) -> Int {
        guard
            let ble,
            let key = layerKey(
                layerIndex: layerIndex,
                ble: ble
            )
        else {
            return 0
        }

        return layerRecords[key]?.activations ?? 0
    }

    func dwellSeconds(
        for layerIndex: Int
    ) -> Double {
        guard
            let ble,
            let key = layerKey(
                layerIndex: layerIndex,
                ble: ble
            )
        else {
            return 0
        }

        var seconds =
            layerRecords[key]?.dwellSeconds ?? 0

        if
            canTrack,
            trackedLayerIndex == layerIndex,
            let startedAt = dwellStartedAt
        {
            seconds +=
                Date().timeIntervalSince(
                    startedAt
                )
        }

        return max(0, seconds)
    }

    func averageDwellSeconds(
        for layerIndex: Int
    ) -> Double? {
        let activations =
            activations(
                for: layerIndex
            )

        guard activations > 0 else {
            return nil
        }

        return
            dwellSeconds(
                for: layerIndex
            ) /
            Double(activations)
    }

    func usageShare(
        for layerIndex: Int
    ) -> Double {
        guard let ble else {
            return 0
        }

        let total =
            ble.layerNames.indices.reduce(
                0.0
            ) {
                partial,
                index in

                partial +
                    dwellSeconds(
                        for: index
                    )
            }

        guard total > 0 else {
            return 0
        }

        let share =
            dwellSeconds(
                for: layerIndex
            ) / total

        // The active layer's live dwell time advances between calculating
        // the total above and calculating this numerator. That can produce
        // a tiny value above 1.0 (for example 1.000002), which SwiftUI's
        // ProgressView correctly warns is out of bounds.
        return min(
            1.0,
            max(0.0, share)
        )
    }

    func keyUsage(
        for layerIndex: Int
    ) -> [KeyUsageSummary] {
        guard
            let ble,
            layerIndex >= 0,
            layerIndex < ble.layerLabels.count
        else {
            return []
        }

        let layerID =
            resolvedLayerID(
                layerIndex: layerIndex,
                ble: ble
            )

        let labels =
            ble.layerLabels[layerIndex]

        return labels.enumerated()
            .compactMap {
                position,
                rawLabel -> KeyUsageSummary? in

                let label =
                    rawLabel.trimmingCharacters(
                        in: .whitespacesAndNewlines
                    )

                guard !label.isEmpty else {
                    return nil
                }

                let key =
                    keyUsageKey(
                        keyboard:
                            ble.keyboardStorageIdentifier,
                        layerID: layerID,
                        position: position,
                        label: label
                    )

                let count =
                    keyRecords[key]?.count ?? 0

                return KeyUsageSummary(
                    position: position,
                    label: label,
                    count: count
                )
            }
            .sorted {
                if $0.count != $1.count {
                    return $0.count > $1.count
                }

                return $0.position < $1.position
            }
    }

    func usageImportance(
        for layerIndex: Int,
        position: Int,
        label: String
    ) -> Double {
        guard
            let ble,
            layerIndex >= 0,
            layerIndex <
                ble.layerLabels.count
        else {
            return 0
        }

        let cleanLabel =
            label.trimmingCharacters(
                in:
                    .whitespacesAndNewlines
            )

        guard !cleanLabel.isEmpty else {
            return 0
        }

        let layerID =
            resolvedLayerID(
                layerIndex:
                    layerIndex,
                ble: ble
            )

        let key =
            keyUsageKey(
                keyboard:
                    ble.keyboardStorageIdentifier,
                layerID: layerID,
                position: position,
                label: cleanLabel
            )

        let count =
            keyRecords[key]?.count ?? 0

        let maximum =
            keyUsage(
                for: layerIndex
            )
            .map(\.count)
            .max()
            ?? 0

        guard maximum > 0 else {
            return 0
        }

        /*
         * Use the same square-root normalization as the heatmap. This avoids
         * one dominant key flattening the rest of the layer's usefulness.
         */
        let normalized =
            sqrt(
                Double(count) /
                Double(maximum)
            )

        return min(
            1.0,
            max(0.0, normalized)
        )
    }


    func heatLevel(
        for layerIndex: Int,
        position: Int,
        label: String
    ) -> Double {
        guard
            let ble,
            layerIndex >= 0,
            layerIndex < ble.layerLabels.count
        else {
            return 0
        }

        let cleanLabel =
            label.trimmingCharacters(
                in: .whitespacesAndNewlines
            )

        guard !cleanLabel.isEmpty else {
            return 0
        }

        let layerID =
            resolvedLayerID(
                layerIndex: layerIndex,
                ble: ble
            )

        let key =
            keyUsageKey(
                keyboard:
                    ble.keyboardStorageIdentifier,
                layerID: layerID,
                position: position,
                label: cleanLabel
            )

        let count =
            keyRecords[key]?.count ?? 0

        guard count > 0 else {
            return 0
        }

        let maximum =
            keyUsage(
                for: layerIndex
            )
            .map(\.count)
            .max()
            ?? 0

        guard maximum > 0 else {
            return 0
        }

        /*
         * Square-root scaling keeps medium-frequency keys visually useful
         * instead of letting one extremely common key dominate the layer.
         */
        let normalized =
            sqrt(
                Double(count) /
                Double(maximum)
            )

        return min(
            1.0,
            max(0.0, normalized)
        )
    }

    func heatCount(
        for layerIndex: Int,
        position: Int,
        label: String
    ) -> Int {
        guard
            let ble,
            layerIndex >= 0,
            layerIndex < ble.layerLabels.count
        else {
            return 0
        }

        let cleanLabel =
            label.trimmingCharacters(
                in: .whitespacesAndNewlines
            )

        guard !cleanLabel.isEmpty else {
            return 0
        }

        let layerID =
            resolvedLayerID(
                layerIndex: layerIndex,
                ble: ble
            )

        let key =
            keyUsageKey(
                keyboard:
                    ble.keyboardStorageIdentifier,
                layerID: layerID,
                position: position,
                label: cleanLabel
            )

        return keyRecords[key]?.count ?? 0
    }


    func resetAllUsage() {
        guard let ble else {
            return
        }

        flushCurrentDwell()

        let keyboardPrefix =
            "\(ble.keyboardStorageIdentifier)|"

        layerRecords =
            layerRecords.filter {
                !$0.key.hasPrefix(
                    keyboardPrefix
                )
            }

        keyRecords =
            keyRecords.filter {
                !$0.key.hasPrefix(
                    keyboardPrefix
                )
            }

        saveNow()

        if canTrack {
            trackedLayerIndex =
                ble.activeLayer
            dwellStartedAt = Date()
        }
    }

    func flushCurrentDwell() {
        commitCurrentDwell(
            restart: false
        )
        saveNow()
    }


    // MARK: - Live tracking

    private var canTrack: Bool {
        runtimeReady && !practiceActive
    }

    private func handleRuntimeReady(
        _ ready: Bool
    ) {
        guard
            runtimeReady != ready
        else {
            return
        }

        if runtimeReady {
            commitCurrentDwell(
                restart: false
            )
            saveNow()
        }

        runtimeReady = ready

        guard
            let ble,
            canTrack
        else {
            trackedLayerIndex = nil
            dwellStartedAt = nil
            return
        }

        trackedLayerIndex =
            ble.activeLayer
        dwellStartedAt = Date()
    }

    private func handlePracticeActive(
        _ active: Bool
    ) {
        guard
            practiceActive != active
        else {
            return
        }

        if !practiceActive && active {
            commitCurrentDwell(
                restart: false
            )
            scheduleSave()
        }

        practiceActive = active

        guard
            let ble,
            canTrack
        else {
            trackedLayerIndex = nil
            dwellStartedAt = nil
            return
        }

        // Practice just ended. Resume passive tracking without counting this
        // as a real-world layer activation.
        trackedLayerIndex =
            ble.activeLayer
        dwellStartedAt = Date()
    }

    private func handleLayerChange(
        _ newLayerIndex: Int
    ) {
        guard
            let ble,
            canTrack
        else {
            return
        }

        if trackedLayerIndex == nil {
            trackedLayerIndex =
                newLayerIndex
            dwellStartedAt = Date()
            return
        }

        guard
            trackedLayerIndex !=
                newLayerIndex
        else {
            return
        }

        commitCurrentDwell(
            restart: false
        )

        incrementActivation(
            layerIndex:
                newLayerIndex,
            ble: ble
        )

        trackedLayerIndex =
            newLayerIndex
        dwellStartedAt = Date()

        scheduleSave()
    }

    private func handlePressedKeys(
        _ pressedKeys: Set<Int>
    ) {
        defer {
            previousPressedKeys =
                pressedKeys
        }

        guard
            let ble,
            canTrack
        else {
            return
        }

        let newlyPressed =
            pressedKeys.subtracting(
                previousPressedKeys
            )

        guard !newlyPressed.isEmpty else {
            return
        }

        let layerIndex =
            ble.activeLayer

        guard
            layerIndex >= 0,
            layerIndex <
                ble.layerLabels.count
        else {
            return
        }

        let layerID =
            resolvedLayerID(
                layerIndex:
                    layerIndex,
                ble: ble
            )

        for position in newlyPressed {
            guard
                position >= 0,
                position <
                    ble.layerLabels[layerIndex]
                        .count
            else {
                continue
            }

            let label =
                ble.layerLabels[layerIndex][position]
                    .trimmingCharacters(
                        in: .whitespacesAndNewlines
                    )

            guard !label.isEmpty else {
                continue
            }

            let key =
                keyUsageKey(
                    keyboard:
                        ble.keyboardStorageIdentifier,
                    layerID: layerID,
                    position: position,
                    label: label
                )

            var record =
                keyRecords[key]
                ?? KeyUsageRecord(
                    count: 0,
                    latestLabel: label
                )

            record.count += 1
            record.latestLabel = label
            keyRecords[key] = record
        }

        scheduleSave()
    }

    private func commitCurrentDwell(
        restart: Bool
    ) {
        guard
            let ble,
            let layerIndex =
                trackedLayerIndex,
            let startedAt =
                dwellStartedAt
        else {
            if restart {
                dwellStartedAt = Date()
            }
            return
        }

        let elapsed =
            max(
                0,
                Date().timeIntervalSince(
                    startedAt
                )
            )

        if let key =
            layerKey(
                layerIndex:
                    layerIndex,
                ble: ble
            ) {
            var record =
                layerRecords[key]
                ?? LayerUsageRecord()

            record.dwellSeconds +=
                elapsed

            if layerIndex >= 0,
               layerIndex <
                    ble.layerNames.count {
                record.latestName =
                    ble.layerNames[layerIndex]
            }

            layerRecords[key] = record
        }

        if restart && canTrack {
            dwellStartedAt = Date()
        } else {
            dwellStartedAt = nil
        }
    }

    private func incrementActivation(
        layerIndex: Int,
        ble: BLETransport
    ) {
        guard let key =
            layerKey(
                layerIndex:
                    layerIndex,
                ble: ble
            )
        else {
            return
        }

        var record =
            layerRecords[key]
            ?? LayerUsageRecord()

        record.activations += 1

        if layerIndex >= 0,
           layerIndex <
                ble.layerNames.count {
            record.latestName =
                ble.layerNames[layerIndex]
        }

        layerRecords[key] = record
    }


    // MARK: - Persistent storage

    private func resolvedLayerID(
        layerIndex: Int,
        ble: BLETransport
    ) -> Int {
        if layerIndex >= 0,
           layerIndex <
                ble.layerIDs.count {
            return ble.layerIDs[layerIndex]
        }

        return layerIndex
    }

    private func layerKey(
        layerIndex: Int,
        ble: BLETransport
    ) -> String? {
        guard
            layerIndex >= 0,
            layerIndex <
                ble.layerNames.count
        else {
            return nil
        }

        let layerID =
            resolvedLayerID(
                layerIndex:
                    layerIndex,
                ble: ble
            )

        return
            "\(ble.keyboardStorageIdentifier)|\(layerID)"
    }

    private func keyUsageKey(
        keyboard: String,
        layerID: Int,
        position: Int,
        label: String
    ) -> String {
        [
            keyboard,
            String(layerID),
            String(position),
            label
        ]
        .joined(separator: "|")
    }

    private func currentKeyboardKeyRecords()
        -> [String: KeyUsageRecord]
    {
        guard let ble else {
            return [:]
        }

        let prefix =
            "\(ble.keyboardStorageIdentifier)|"

        return keyRecords.filter {
            $0.key.hasPrefix(prefix)
        }
    }

    private func load() {
        if let data =
            defaults.data(
                forKey:
                    layerDefaultsKey
            ) {
            do {
                layerRecords =
                    try JSONDecoder().decode(
                        [String: LayerUsageRecord].self,
                        from: data
                    )
            } catch {
                print(
                    "Failed to load layer usage:",
                    error
                )
            }
        }

        if let data =
            defaults.data(
                forKey:
                    keyDefaultsKey
            ) {
            do {
                keyRecords =
                    try JSONDecoder().decode(
                        [String: KeyUsageRecord].self,
                        from: data
                    )
            } catch {
                print(
                    "Failed to load key usage:",
                    error
                )
            }
        }
    }

    private func scheduleSave() {
        saveWorkItem?.cancel()

        let workItem =
            DispatchWorkItem { [weak self] in
                self?.saveNow()
            }

        saveWorkItem = workItem

        DispatchQueue.main.asyncAfter(
            deadline: .now() + 1.5,
            execute: workItem
        )
    }

    private func saveNow() {
        saveWorkItem?.cancel()
        saveWorkItem = nil

        do {
            let layerData =
                try JSONEncoder().encode(
                    layerRecords
                )

            defaults.set(
                layerData,
                forKey:
                    layerDefaultsKey
            )

            let keyData =
                try JSONEncoder().encode(
                    keyRecords
                )

            defaults.set(
                keyData,
                forKey:
                    keyDefaultsKey
            )
        } catch {
            print(
                "Failed to save usage analytics:",
                error
            )
        }
    }
}


struct UsageStatisticsView: View {
    @ObservedObject var ble: BLETransport
    @ObservedObject var usage: UsageAnalyticsState

    @State private var selectedLayerIndex = 0

    var body: some View {
        VStack(
            alignment: .leading,
            spacing: 14
        ) {
            HStack {
                Text("Usage Statistics")
                    .font(.title2.bold())

                Spacer()

                Text("Practice excluded")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if ble.layerNames.isEmpty {
                Spacer()

                Text(
                    "Refresh the keymap first."
                )
                .foregroundStyle(.secondary)
                .frame(
                    maxWidth: .infinity
                )

                Spacer()

            } else {
                layerOverview

                Divider()

                selectedLayerSection

                Spacer()

                HStack {
                    Text(
                        "\(usage.totalKeyPresses) recorded key presses"
                    )
                    .font(.caption)
                    .foregroundStyle(.secondary)

                    Spacer()

                    Button(
                        "Reset Usage Data",
                        role: .destructive
                    ) {
                        usage.resetAllUsage()
                    }
                }
            }
        }
        .padding(18)
        .frame(
            minWidth: 520,
            idealWidth: 560,
            minHeight: 500,
            idealHeight: 560
        )
        .onChange(
            of: ble.layerNames.count
        ) { _ in
            if selectedLayerIndex >=
                ble.layerNames.count {
                selectedLayerIndex = 0
            }
        }
    }

    private var layerOverview: some View {
        VStack(
            alignment: .leading,
            spacing: 8
        ) {
            Text("Layers")
                .font(.headline)

            ForEach(
                Array(
                    ble.layerNames.enumerated()
                ),
                id: \.offset
            ) { index, name in
                HStack(spacing: 10) {
                    Text(name)
                        .frame(
                            width: 100,
                            alignment: .leading
                        )

                    ProgressView(
                        value:
                            usage.usageShare(
                                for: index
                            )
                    )
                    .frame(maxWidth: .infinity)

                    Text(
                        percent(
                            usage.usageShare(
                                for: index
                            )
                        )
                    )
                    .monospacedDigit()
                    .frame(
                        width: 48,
                        alignment: .trailing
                    )

                    Text(
                        "\(usage.activations(for: index))×"
                    )
                    .monospacedDigit()
                    .foregroundStyle(.secondary)
                    .frame(
                        width: 48,
                        alignment: .trailing
                    )
                }
            }
        }
    }

    private var selectedLayerSection: some View {
        VStack(
            alignment: .leading,
            spacing: 10
        ) {
            HStack {
                Picker(
                    "Layer",
                    selection:
                        $selectedLayerIndex
                ) {
                    ForEach(
                        Array(
                            ble.layerNames.enumerated()
                        ),
                        id: \.offset
                    ) { index, name in
                        Text(name)
                            .tag(index)
                    }
                }
                .frame(maxWidth: 240)

                Spacer()

                VStack(
                    alignment: .trailing,
                    spacing: 2
                ) {
                    Text(
                        duration(
                            usage.dwellSeconds(
                                for:
                                    selectedLayerIndex
                            )
                        )
                    )
                    .monospacedDigit()

                    Text("recorded dwell")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                VStack(
                    alignment: .trailing,
                    spacing: 2
                ) {
                    Text(
                        averageDwellText
                    )
                    .monospacedDigit()

                    Text("avg / activation")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            let keys =
                usage.keyUsage(
                    for:
                        selectedLayerIndex
                )

            if keys.isEmpty {
                Text(
                    "No key usage recorded for this layer yet."
                )
                .foregroundStyle(.secondary)
            } else {
                Text("Most used keys")
                    .font(.headline)

                ForEach(
                    Array(keys.prefix(8))
                ) { key in
                    HStack {
                        Text(key.label)
                            .lineLimit(1)

                        Spacer()

                        Text(
                            "\(key.count)"
                        )
                        .monospacedDigit()
                        .foregroundStyle(.secondary)
                    }
                }

                let usedKeys =
                    keys.filter {
                        $0.count > 0
                    }

                if usedKeys.count > 8 {
                    Text(
                        "\(usedKeys.count) keys used on this layer"
                    )
                    .font(.caption)
                    .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var averageDwellText: String {
        guard
            let value =
                usage.averageDwellSeconds(
                    for:
                        selectedLayerIndex
                )
        else {
            return "—"
        }

        return duration(value)
    }

    private func percent(
        _ value: Double
    ) -> String {
        String(
            format: "%.0f%%",
            value * 100.0
        )
    }

    private func duration(
        _ seconds: Double
    ) -> String {
        if seconds < 60 {
            return String(
                format: "%.1fs",
                seconds
            )
        }

        let minutes =
            seconds / 60.0

        if minutes < 60 {
            return String(
                format: "%.1fm",
                minutes
            )
        }

        return String(
            format: "%.1fh",
            minutes / 60.0
        )
    }
}

