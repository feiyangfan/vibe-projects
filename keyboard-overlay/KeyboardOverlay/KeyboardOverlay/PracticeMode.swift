//
//  PracticeMode.swift
//  KeyboardOverlay
//
//  Dynamic keymap practice built from the same cached metadata used by
//  the overlay. No layer names or key positions are hard-coded.
//

import Foundation
import SwiftUI
import Combine

final class PracticeState: ObservableObject {
    @Published var isActive = false
    @Published var selectedLayerIndex = 0

    @Published private(set) var targetPosition: Int?
    @Published private(set) var targetLabel = ""

    @Published var hideOverlayLabels = false
    @Published var showTargetHint = true

    @Published private(set) var correctCount = 0
    @Published private(set) var wrongCount = 0
    @Published private(set) var lastResult = ""

    private weak var ble: BLETransport?
    private var previousPressedKeys: Set<Int> = []
    private var cancellables = Set<AnyCancellable>()
    private var targetGeneration = 0

    init(ble: BLETransport) {
        self.ble = ble
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

                // A refreshed keymap can change the candidate positions.
                if self.isActive {
                    self.chooseNextTarget()
                }
            }
            .store(in: &cancellables)
    }

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
            lastResult = "No practiceable keys on this layer"
            isActive = false
            return
        }

        correctCount = 0
        wrongCount = 0
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
        lastResult = ""
    }

    func resetStats() {
        correctCount = 0
        wrongCount = 0
        lastResult = ""
    }

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
            lastResult = "No practiceable keys on this layer"
            return
        }

        let previousTarget = targetPosition

        let choices: [(position: Int, label: String)]

        if candidates.count > 1,
           let previousTarget {
            choices = candidates.filter {
                $0.position != previousTarget
            }
        } else {
            choices = candidates
        }

        guard let target = choices.randomElement() else {
            return
        }

        targetGeneration += 1
        targetPosition = target.position
        targetLabel = target.label
    }

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
         * For a non-base layer, the layer activation key is normally pressed
         * while another layer is active. Ignore those presses. A quiz attempt
         * only begins once Companion F21 says the requested layer is active.
         */
        guard ble.activeLayer == selectedLayerIndex else {
            return
        }

        for position in newlyPressed.sorted() {
            if position == targetPosition {
                correctCount += 1
                lastResult = "Correct ✓"

                let completedGeneration =
                    targetGeneration

                DispatchQueue.main.asyncAfter(
                    deadline: .now() + 0.35
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

            let actualLabel =
                label(
                    for: position,
                    layerIndex: selectedLayerIndex,
                    ble: ble
                )

            if actualLabel.isEmpty {
                lastResult = "Wrong key"
            } else {
                lastResult =
                    "Wrong — \(actualLabel)"
            }
        }
    }

    private func practiceCandidates(
        layerIndex: Int,
        ble: BLETransport
    ) -> [(position: Int, label: String)] {
        guard
            layerIndex >= 0,
            layerIndex < ble.layerLabels.count
        else {
            return []
        }

        let labels = ble.layerLabels[layerIndex]
        let physicalPositions =
            Set(ble.physicalKeys.map(\.id))

        let layerOnlyLabels =
            Set(ble.layerNames)

        return labels.enumerated().compactMap {
            position,
            rawLabel in

            let label =
                rawLabel.trimmingCharacters(
                    in: .whitespacesAndNewlines
                )

            guard
                physicalPositions.contains(position),
                !label.isEmpty,
                label != "Unknown",
                label != "Transparent",
                !layerOnlyLabels.contains(label)
            else {
                return nil
            }

            return (
                position: position,
                label: label
            )
        }
    }

    private func label(
        for position: Int,
        layerIndex: Int,
        ble: BLETransport
    ) -> String {
        guard
            layerIndex >= 0,
            layerIndex < ble.layerLabels.count,
            position >= 0,
            position < ble.layerLabels[layerIndex].count
        else {
            return ""
        }

        return ble.layerLabels[layerIndex][position]
    }
}


struct PracticeModeView: View {
    @ObservedObject var ble: BLETransport
    @ObservedObject var practice: PracticeState

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
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

            GroupBox {
                VStack(spacing: 8) {
                    if practice.isActive {
                        Text(
                            ble.activeLayer ==
                                practice.selectedLayerIndex
                            ? "Press"
                            : "Activate \(practice.selectedLayerName), then press"
                        )
                        .font(.callout)
                        .foregroundStyle(.secondary)

                        Text(practice.targetLabel)
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
                                minHeight: 54
                            )

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
                            : "Choose any layer from the current cached keymap and start."
                        )
                        .foregroundStyle(.secondary)
                        .frame(
                            maxWidth: .infinity,
                            minHeight: 100
                        )
                    }
                }
                .padding(8)
            }

            HStack(spacing: 22) {
                stat(
                    title: "Correct",
                    value: "\(practice.correctCount)"
                )

                stat(
                    title: "Wrong",
                    value: "\(practice.wrongCount)"
                )

                stat(
                    title: "Accuracy",
                    value: practice.accuracyText
                )

                Spacer()

                Button("Reset Stats") {
                    practice.resetStats()
                }
                .disabled(
                    practice.totalAttempts == 0
                )
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
                "Practice uses the same cached layers and labels as the overlay. After changing the keymap in ZMK Studio, use Refresh Keymap and the available practice layers/targets update automatically."
            )
            .font(.caption)
            .foregroundStyle(.secondary)

            Spacer()
        }
        .padding(18)
        .frame(
            width: 480,
            height: 410
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
        VStack(alignment: .leading, spacing: 2) {
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
