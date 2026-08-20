import SwiftUI
import AppKit

final class OverlayUIState: ObservableObject {
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

                    let displayLabel =
                        isModifierHold
                        ? ble.holdModifierLabel(at: key.id)
                        : label

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
                                : Color.white
                                    .opacity(uiState.normalBorderOpacity),
                            lineWidth: max(
                                0.5,
                                (
                                    isModifierHold
                                    ? uiState.modifierHoldBorderWidth
                                    : isPressed
                                        ? uiState.pressedBorderWidth
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
