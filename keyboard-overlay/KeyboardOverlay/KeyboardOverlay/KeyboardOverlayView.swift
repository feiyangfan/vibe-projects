import SwiftUI
import AppKit

final class OverlayUIState: ObservableObject {
    enum AppearancePreset: String, CaseIterable, Identifiable {
        case balanced
        case minimal
        case highContrast

        var id: String { rawValue }

        var title: String {
            switch self {
            case .balanced:
                return "Balanced"
            case .minimal:
                return "Minimal"
            case .highContrast:
                return "High Contrast"
            }
        }
    }

    @Published var isEditing = false

    @Published var overlayOpacity: Double {
        didSet { defaults.set(overlayOpacity, forKey: Keys.overlayOpacity) }
    }

    @Published var normalFillOpacity: Double {
        didSet { defaults.set(normalFillOpacity, forKey: Keys.normalFillOpacity) }
    }

    @Published var normalBorderOpacity: Double {
        didSet { defaults.set(normalBorderOpacity, forKey: Keys.normalBorderOpacity) }
    }

    @Published var normalTextColor: Color {
        didSet { saveColor(normalTextColor, key: Keys.normalTextColor) }
    }

    @Published var textShadowOpacity: Double {
        didSet { defaults.set(textShadowOpacity, forKey: Keys.textShadowOpacity) }
    }

    @Published var practiceTargetFillOpacity: Double {
        didSet {
            defaults.set(
                practiceTargetFillOpacity,
                forKey: Keys.practiceTargetFillOpacity
            )
        }
    }

    @Published var pressedFillColor: Color {
        didSet { saveColor(pressedFillColor, key: Keys.pressedFillColor) }
    }

    @Published var pressedFillOpacity: Double {
        didSet { defaults.set(pressedFillOpacity, forKey: Keys.pressedFillOpacity) }
    }

    @Published var pressedBorderColor: Color {
        didSet { saveColor(pressedBorderColor, key: Keys.pressedBorderColor) }
    }

    @Published var pressedBorderWidth: Double {
        didSet { defaults.set(pressedBorderWidth, forKey: Keys.pressedBorderWidth) }
    }

    @Published var pressedTextColor: Color {
        didSet { saveColor(pressedTextColor, key: Keys.pressedTextColor) }
    }

    @Published var modifierHoldFillColor: Color {
        didSet { saveColor(modifierHoldFillColor, key: Keys.modifierHoldFillColor) }
    }

    @Published var modifierHoldFillOpacity: Double {
        didSet { defaults.set(modifierHoldFillOpacity, forKey: Keys.modifierHoldFillOpacity) }
    }

    @Published var modifierHoldBorderColor: Color {
        didSet { saveColor(modifierHoldBorderColor, key: Keys.modifierHoldBorderColor) }
    }

    @Published var modifierHoldBorderWidth: Double {
        didSet { defaults.set(modifierHoldBorderWidth, forKey: Keys.modifierHoldBorderWidth) }
    }

    @Published var modifierHoldTextColor: Color {
        didSet { saveColor(modifierHoldTextColor, key: Keys.modifierHoldTextColor) }
    }

    private let defaults = UserDefaults.standard

    private enum Keys {
        static let overlayOpacity = "OverlayAppearance.overlayOpacity"
        static let normalFillOpacity = "OverlayAppearance.normalFillOpacity"
        static let normalBorderOpacity = "OverlayAppearance.normalBorderOpacity"
        static let normalTextColor = "OverlayAppearance.normalTextColor"
        static let textShadowOpacity = "OverlayAppearance.textShadowOpacity"
        static let practiceTargetFillOpacity = "OverlayAppearance.practiceTargetFillOpacity"
        static let pressedFillColor = "OverlayAppearance.pressedFillColor"
        static let pressedFillOpacity = "OverlayAppearance.pressedFillOpacity"
        static let pressedBorderColor = "OverlayAppearance.pressedBorderColor"
        static let pressedBorderWidth = "OverlayAppearance.pressedBorderWidth"
        static let pressedTextColor = "OverlayAppearance.pressedTextColor"
        static let modifierHoldFillColor = "OverlayAppearance.modifierHoldFillColor"
        static let modifierHoldFillOpacity = "OverlayAppearance.modifierHoldFillOpacity"
        static let modifierHoldBorderColor = "OverlayAppearance.modifierHoldBorderColor"
        static let modifierHoldBorderWidth = "OverlayAppearance.modifierHoldBorderWidth"
        static let modifierHoldTextColor = "OverlayAppearance.modifierHoldTextColor"
    }

    init() {
        overlayOpacity =
            defaults.object(forKey: Keys.overlayOpacity) as? Double ?? 1.0

        normalFillOpacity =
            defaults.object(forKey: Keys.normalFillOpacity) as? Double ?? 0.15

        normalBorderOpacity =
            defaults.object(forKey: Keys.normalBorderOpacity) as? Double ?? 0.40

        normalTextColor =
            Self.loadColor(defaults: defaults, key: Keys.normalTextColor) ?? .white

        textShadowOpacity =
            defaults.object(forKey: Keys.textShadowOpacity) as? Double ?? 0.0

        practiceTargetFillOpacity =
            defaults.object(forKey: Keys.practiceTargetFillOpacity) as? Double ?? 0.40

        pressedFillColor =
            Self.loadColor(defaults: defaults, key: Keys.pressedFillColor)
            ?? Color(nsColor: .systemBlue)

        pressedFillOpacity =
            defaults.object(forKey: Keys.pressedFillOpacity) as? Double ?? 0.78

        pressedBorderColor =
            Self.loadColor(defaults: defaults, key: Keys.pressedBorderColor) ?? .white

        pressedBorderWidth =
            defaults.object(forKey: Keys.pressedBorderWidth) as? Double ?? 2.0

        pressedTextColor =
            Self.loadColor(defaults: defaults, key: Keys.pressedTextColor) ?? .white

        modifierHoldFillColor =
            Self.loadColor(defaults: defaults, key: Keys.modifierHoldFillColor)
            ?? Color(nsColor: .systemOrange)

        modifierHoldFillOpacity =
            defaults.object(forKey: Keys.modifierHoldFillOpacity) as? Double ?? 0.88

        modifierHoldBorderColor =
            Self.loadColor(defaults: defaults, key: Keys.modifierHoldBorderColor)
            ?? .white

        modifierHoldBorderWidth =
            defaults.object(forKey: Keys.modifierHoldBorderWidth) as? Double ?? 2.5

        modifierHoldTextColor =
            Self.loadColor(defaults: defaults, key: Keys.modifierHoldTextColor) ?? .white
    }

    func resetAppearance() {
        overlayOpacity = 1.0
        normalFillOpacity = 0.15
        normalBorderOpacity = 0.40
        normalTextColor = .white
        textShadowOpacity = 0.0
        practiceTargetFillOpacity = 0.40

        pressedFillColor = Color(nsColor: .systemBlue)
        pressedFillOpacity = 0.78
        pressedBorderColor = .white
        pressedBorderWidth = 2.0
        pressedTextColor = .white

        modifierHoldFillColor = Color(nsColor: .systemOrange)
        modifierHoldFillOpacity = 0.88
        modifierHoldBorderColor = .white
        modifierHoldBorderWidth = 2.5
        modifierHoldTextColor = .white
    }

    func applyPreset(_ preset: AppearancePreset) {
        // Keep overall opacity at 100% so labels remain crisp. The presets
        // reduce per-key visual mass instead of fading the entire overlay.
        overlayOpacity = 1.0

        switch preset {
        case .balanced:
            normalFillOpacity = 0.28
            normalBorderOpacity = 0.18
            normalTextColor = .white.opacity(0.92)
            textShadowOpacity = 0.55
            practiceTargetFillOpacity = 0.45

            pressedFillColor = .white
            pressedFillOpacity = 0.22
            pressedBorderColor = .white.opacity(0.30)
            pressedBorderWidth = 1.5
            pressedTextColor = .white.opacity(0.98)

            modifierHoldFillColor = Color(nsColor: .systemOrange)
            modifierHoldFillOpacity = 0.45
            modifierHoldBorderColor = .white.opacity(0.34)
            modifierHoldBorderWidth = 1.75
            modifierHoldTextColor = .white

        case .minimal:
            normalFillOpacity = 0.16
            normalBorderOpacity = 0.10
            normalTextColor = .white.opacity(0.88)
            textShadowOpacity = 0.48
            practiceTargetFillOpacity = 0.32

            pressedFillColor = .white
            pressedFillOpacity = 0.18
            pressedBorderColor = .white.opacity(0.22)
            pressedBorderWidth = 1.25
            pressedTextColor = .white.opacity(0.94)

            modifierHoldFillColor = Color(nsColor: .systemOrange)
            modifierHoldFillOpacity = 0.32
            modifierHoldBorderColor = .white.opacity(0.26)
            modifierHoldBorderWidth = 1.5
            modifierHoldTextColor = .white.opacity(0.95)

        case .highContrast:
            normalFillOpacity = 0.38
            normalBorderOpacity = 0.24
            normalTextColor = .white
            textShadowOpacity = 0.65
            practiceTargetFillOpacity = 0.55

            pressedFillColor = .white
            pressedFillOpacity = 0.30
            pressedBorderColor = .white.opacity(0.45)
            pressedBorderWidth = 2.0
            pressedTextColor = .white

            modifierHoldFillColor = Color(nsColor: .systemOrange)
            modifierHoldFillOpacity = 0.55
            modifierHoldBorderColor = .white.opacity(0.50)
            modifierHoldBorderWidth = 2.25
            modifierHoldTextColor = .white
        }
    }

    private func saveColor(_ color: Color, key: String) {
        guard let nsColor = NSColor(color).usingColorSpace(.deviceRGB) else {
            return
        }

        defaults.set(
            [
                Double(nsColor.redComponent),
                Double(nsColor.greenComponent),
                Double(nsColor.blueComponent),
                Double(nsColor.alphaComponent)
            ],
            forKey: key
        )
    }

    private static func loadColor(
        defaults: UserDefaults,
        key: String
    ) -> Color? {
        guard
            let components = defaults.array(forKey: key) as? [Double],
            components.count == 4
        else {
            return nil
        }

        return Color(
            nsColor: NSColor(
                red: components[0],
                green: components[1],
                blue: components[2],
                alpha: components[3]
            )
        )
    }
}

struct KeyboardOverlayView: View {
    @ObservedObject var ble: BLETransport
    @ObservedObject var uiState: OverlayUIState
    @ObservedObject var practice: PracticeState
    @ObservedObject var usage: UsageAnalyticsState

    private let referenceSize = CGSize(width: 900, height: 330)

    var body: some View {
        GeometryReader { geometry in
            let widthScale = geometry.size.width / referenceSize.width
            let heightScale = geometry.size.height / referenceSize.height
            let scale = max(0.01, min(widthScale, heightScale))

            let scaledWidth = referenceSize.width * scale
            let scaledHeight = referenceSize.height * scale
            let offsetX = (geometry.size.width - scaledWidth) / 2
            let offsetY = (geometry.size.height - scaledHeight) / 2

            ZStack(alignment: .topLeading) {
                ForEach(ble.physicalKeys) { key in
                    let label =
                        ble.activeLayer < ble.layerLabels.count &&
                        key.id < ble.layerLabels[ble.activeLayer].count
                        ? ble.layerLabels[ble.activeLayer][key.id]
                        : ""

                    let isPressed = ble.pressedKeys.contains(key.id)
                    let isModifierHold =
                        ble.isResolvedModifierHold(at: key.id)

                    let isPracticeTarget =
                        practice.isActive &&
                        practice.showTargetHint &&
                        practice.targetPosition == key.id

                    let heatLevel =
                        usage.showHeatmap
                        ? usage.heatLevel(
                            for: ble.activeLayer,
                            position: key.id,
                            label: label
                        )
                        : 0

                    let isHeatmapped =
                        usage.showHeatmap &&
                        heatLevel > 0

                    let baseDisplayLabel =
                        isModifierHold
                        ? ble.holdModifierLabel(at: key.id)
                        : label

                    let displayLabel =
                        practice.isActive &&
                        practice.hideOverlayLabels &&
                        !isPressed &&
                        !isModifierHold
                        ? ""
                        : baseDisplayLabel

                    let keyWidth = key.width * scale
                    let keyHeight = key.height * scale

                    ZStack {
                        RoundedRectangle(
                            cornerRadius: max(2, 7 * scale)
                        )
                        .fill(
                            isModifierHold
                            ? uiState.modifierHoldFillColor
                                .opacity(uiState.modifierHoldFillOpacity)
                            : isPressed
                                ? uiState.pressedFillColor
                                    .opacity(uiState.pressedFillOpacity)
                                : isPracticeTarget
                                    ? Color(nsColor: .systemGreen)
                                        .opacity(uiState.practiceTargetFillOpacity)
                                    : isHeatmapped
                                        ? heatmapColor(
                                            level: heatLevel
                                        )
                                        .opacity(
                                            0.18 +
                                            0.62 * heatLevel
                                        )
                                        : Color.black
                                            .opacity(uiState.normalFillOpacity)
                        )

                        RoundedRectangle(
                            cornerRadius: max(2, 7 * scale)
                        )
                        .stroke(
                            isModifierHold
                            ? uiState.modifierHoldBorderColor
                            : isPressed
                                ? uiState.pressedBorderColor
                                : isPracticeTarget
                                    ? Color(nsColor: .systemGreen)
                                    : isHeatmapped
                                        ? heatmapColor(
                                            level: heatLevel
                                        )
                                        .opacity(0.90)
                                        : Color.white
                                            .opacity(uiState.normalBorderOpacity),
                            lineWidth: max(
                                0.5,
                                (
                                    isModifierHold
                                    ? uiState.modifierHoldBorderWidth
                                    : isPressed
                                        ? uiState.pressedBorderWidth
                                        : isPracticeTarget
                                            ? 2.5
                                            : isHeatmapped
                                                ? 1.5
                                                : 1.0
                                ) * scale
                            )
                        )

                        Text(displayLabel)
                            .font(
                                .system(
                                    size: max(7, 14 * scale),
                                    weight: (isPressed || isModifierHold)
                                        ? .bold
                                        : .medium
                                )
                            )
                            .foregroundColor(
                                isModifierHold
                                ? uiState.modifierHoldTextColor
                                : isPressed
                                    ? uiState.pressedTextColor
                                    : uiState.normalTextColor
                            )
                            .shadow(
                                color: Color.black.opacity(
                                    uiState.textShadowOpacity
                                ),
                                radius: max(0.5, 1.2 * scale),
                                x: 0,
                                y: max(0.5, 0.8 * scale)
                            )
                            .multilineTextAlignment(.center)
                            .lineLimit(2)
                            .minimumScaleFactor(0.45)
                            .frame(
                                width: max(1, keyWidth - 6 * scale),
                                height: max(1, keyHeight - 4 * scale)
                            )
                            .allowsHitTesting(false)
                    }
                    .frame(width: keyWidth, height: keyHeight)
                    .rotationEffect(.degrees(key.rotation))
                    .position(
                        x: offsetX + key.x * scale,
                        y: offsetY + key.y * scale
                    )
                    .opacity(uiState.overlayOpacity)
                }

                if usage.showHeatmap &&
                   !practice.isActive &&
                   !uiState.isEditing {
                    Text(
                        "HEATMAP • " +
                        currentLayerName
                    )
                    .font(
                        .system(
                            size: 10,
                            weight: .semibold
                        )
                    )
                    .foregroundColor(.white)
                    .padding(
                        .horizontal,
                        8
                    )
                    .padding(
                        .vertical,
                        4
                    )
                    .background(
                        RoundedRectangle(
                            cornerRadius: 5
                        )
                        .fill(
                            Color.black
                                .opacity(0.62)
                        )
                    )
                    .padding(8)
                    .allowsHitTesting(false)
                }

                if practice.isActive {
                    VStack(spacing: 2) {
                        Text(
                            "PRACTICE • " +
                            practice.selectedLayerName
                        )
                        .font(
                            .system(
                                size: 10,
                                weight: .semibold
                            )
                        )

                        Text(practice.targetLabel)
                            .font(
                                .system(
                                    size: 15,
                                    weight: .bold
                                )
                            )
                    }
                    .foregroundColor(.white)
                    .padding(
                        .horizontal,
                        10
                    )
                    .padding(
                        .vertical,
                        5
                    )
                    .background(
                        RoundedRectangle(
                            cornerRadius: 6
                        )
                        .fill(
                            Color.black
                                .opacity(0.72)
                        )
                    )
                    .frame(
                        maxWidth: .infinity,
                        alignment: .top
                    )
                    .padding(.top, 6)
                    .allowsHitTesting(false)
                }

                if uiState.isEditing {
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(
                            Color.accentColor,
                            style: StrokeStyle(
                                lineWidth: 2,
                                dash: [8, 5]
                            )
                        )
                        .padding(2)
                        .allowsHitTesting(false)

                    VStack(alignment: .leading, spacing: 3) {
                        Text("EDIT • drag to move • resize from edges/corners")
                        Text("Layer \(ble.activeLayer) • \(currentLabelCount) labels")
                    }
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 5)
                    .background(
                        RoundedRectangle(cornerRadius: 5)
                            .fill(Color.black.opacity(0.70))
                    )
                    .padding(8)
                    .allowsHitTesting(false)
                }
            }
            .frame(
                width: geometry.size.width,
                height: geometry.size.height
            )
        }
        .background(Color.clear)
    }

    private var currentLayerName: String {
        guard
            ble.activeLayer >= 0,
            ble.activeLayer < ble.layerNames.count
        else {
            return "Layer"
        }

        return ble.layerNames[ble.activeLayer]
    }

    private func heatmapColor(
        level: Double
    ) -> Color {
        let clamped =
            min(
                1.0,
                max(0.0, level)
            )

        let blended =
            NSColor.systemYellow.blended(
                withFraction:
                    CGFloat(clamped),
                of: NSColor.systemRed
            )
            ?? NSColor.systemOrange

        return Color(
            nsColor: blended
        )
    }

    private var currentLabelCount: Int {
        guard ble.activeLayer < ble.layerLabels.count else {
            return 0
        }
        return ble.layerLabels[ble.activeLayer].count
    }
}

struct OverlayAppearanceView: View {
    @ObservedObject var uiState: OverlayUIState

    var body: some View {
        Form {
            Section("Presets") {
                HStack(spacing: 8) {
                    ForEach(
                        OverlayUIState.AppearancePreset.allCases
                    ) { preset in
                        Button(preset.title) {
                            uiState.applyPreset(preset)
                        }
                        .buttonStyle(.bordered)
                    }
                }

                Text(
                    "Balanced is the recommended starting point. Minimal keeps the background most visible; High Contrast favors label readability."
                )
                .font(.caption)
                .foregroundStyle(.secondary)
            }

            Section("Overlay") {
                sliderRow(
                    title: "Overall opacity",
                    value: $uiState.overlayOpacity,
                    range: 0.10...1.0
                )
            }

            Section("Normal Keys") {
                sliderRow(
                    title: "Fill opacity",
                    value: $uiState.normalFillOpacity,
                    range: 0.0...1.0
                )

                sliderRow(
                    title: "Border opacity",
                    value: $uiState.normalBorderOpacity,
                    range: 0.0...1.0
                )

                ColorPicker(
                    "Text color",
                    selection: $uiState.normalTextColor,
                    supportsOpacity: true
                )

                sliderRow(
                    title: "Text shadow",
                    value: $uiState.textShadowOpacity,
                    range: 0.0...1.0
                )
            }

            Section("Pressed Keys") {
                ColorPicker(
                    "Fill color",
                    selection: $uiState.pressedFillColor,
                    supportsOpacity: false
                )

                sliderRow(
                    title: "Fill opacity",
                    value: $uiState.pressedFillOpacity,
                    range: 0.0...1.0
                )

                ColorPicker(
                    "Border color",
                    selection: $uiState.pressedBorderColor,
                    supportsOpacity: true
                )

                sliderRow(
                    title: "Border width",
                    value: $uiState.pressedBorderWidth,
                    range: 0.5...5.0
                )

                ColorPicker(
                    "Text color",
                    selection: $uiState.pressedTextColor,
                    supportsOpacity: true
                )
            }

            Section("Resolved Modifier Holds") {
                ColorPicker(
                    "Fill color",
                    selection: $uiState.modifierHoldFillColor,
                    supportsOpacity: false
                )

                sliderRow(
                    title: "Fill opacity",
                    value: $uiState.modifierHoldFillOpacity,
                    range: 0.0...1.0
                )

                ColorPicker(
                    "Border color",
                    selection: $uiState.modifierHoldBorderColor,
                    supportsOpacity: true
                )

                sliderRow(
                    title: "Border width",
                    value: $uiState.modifierHoldBorderWidth,
                    range: 0.5...5.0
                )

                ColorPicker(
                    "Text color",
                    selection: $uiState.modifierHoldTextColor,
                    supportsOpacity: true
                )
            }

            Section("Highlights") {
                sliderRow(
                    title: "Practice target fill",
                    value: $uiState.practiceTargetFillOpacity,
                    range: 0.0...1.0
                )
            }

            HStack {
                Spacer()
                Button("Reset Defaults") {
                    uiState.resetAppearance()
                }
            }
        }
        .formStyle(.grouped)
        .padding(12)
        .frame(width: 420, height: 480)
    }

    @ViewBuilder
    private func sliderRow(
        title: String,
        value: Binding<Double>,
        range: ClosedRange<Double>
    ) -> some View {
        HStack {
            Text(title)

            Slider(value: value, in: range)

            Text(
                value.wrappedValue.formatted(
                    .number.precision(.fractionLength(2))
                )
            )
            .monospacedDigit()
            .frame(width: 42, alignment: .trailing)
        }
    }
}
