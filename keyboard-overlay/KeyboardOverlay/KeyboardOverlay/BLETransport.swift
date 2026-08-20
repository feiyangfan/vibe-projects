//
//  BLETransport.swift
//  KeyboardOverlay
//
//  Created by Feiyang Fan on 2026-08-18.
//

import Foundation
import CoreBluetooth
import SwiftProtobuf


final class BLETransport: NSObject, ObservableObject {
    private var central: CBCentralManager!
    private var peripheral: CBPeripheral?

    private var studioCharacteristic: CBCharacteristic?
    private var layerCharacteristic: CBCharacteristic?
    private var keyEventCharacteristic: CBCharacteristic?
    private var protocolInfoCharacteristic: CBCharacteristic?
    private var modifierStateCharacteristic: CBCharacteristic?

    @Published var status = "Initializing"
    @Published private(set) var connectedDeviceName = "ZMK Keyboard"
    @Published private(set) var hasCachedOverlay = false
    @Published private(set) var keymapCacheDirty = false
    @Published private(set) var isRefreshingKeymap = false
    @Published private(set) var companionProtocolVersion: String?
    @Published private(set) var companionCapabilities: UInt16 = 0
    @Published private(set) var activeModifiers: UInt8 = 0
    @Published private(set) var resolvedModifierHoldPositions: Set<Int> = []

    private var pressSequenceCounter = 0
    private var pressSequenceByPosition: [Int: Int] = [:]

    @Published private(set) var behaviorNames: [UInt32: String] = [:]

    @Published var layerNames: [String] = []
    @Published var layerLabels: [[String]] = []
    @Published private(set) var layerHoldModifierMasks: [[UInt8]] = []
    @Published private(set) var layerHoldModifierLabels: [[String]] = []
    @Published private(set) var layerIDs: [Int] = []
    @Published var activeLayer: Int = 0

    @Published var physicalKeys: [KeyDisplay] = []
    @Published private(set) var pressedKeys: Set<Int> = []

    private var currentKeymap: Zmk_Keymap_Keymap?
    private var lastReportedLayerID: Int?

    // ZMK Studio RPC BLE service.
    private let serviceUUID =
        CBUUID(string: "00000000-0196-6107-C967-C5CFB1C2482A")

    private let characteristicUUID =
        CBUUID(string: "00000001-0196-6107-C967-C5CFB1C2482A")

    // Generic ZMK Overlay Companion BLE service.
    private let companionServiceUUID =
        CBUUID(string: "7D8C5F20-7C8A-4F45-9C84-2F6E8A7B2000")

    private let layerCharacteristicUUID =
        CBUUID(string: "7D8C5F21-7C8A-4F45-9C84-2F6E8A7B2000")

    private let keyEventCharacteristicUUID =
        CBUUID(string: "7D8C5F22-7C8A-4F45-9C84-2F6E8A7B2000")

    private let protocolInfoCharacteristicUUID =
        CBUUID(string: "7D8C5F23-7C8A-4F45-9C84-2F6E8A7B2000")

    private let modifierStateCharacteristicUUID =
        CBUUID(string: "7D8C5F24-7C8A-4F45-9C84-2F6E8A7B2000")

    private var frameCodec = FrameCodec()

    private var pendingBehaviorIDs: [UInt32] = []

    // Overlay-owned Studio RPC request IDs live in a high range so they are
    // unlikely to collide with another Studio client. Responses not matching
    // an ID in this set are ignored.
    private var nextRequestID: UInt32 = 0x8000_0000
    private var ownedRequestIDs: Set<UInt32> = []

    // Manual refresh transaction state.
    private var refreshHasKeymap = false
    private var refreshHasPhysicalLayout = false
    private var refreshBehaviorsComplete = false
    private var refreshLabelsReady = false

    // Behavior metadata is requested one item at a time. Some custom
    // behaviors may be listed by Studio but fail to answer a details request,
    // so keep an in-flight ID and a short timeout rather than stalling forever.
    private var behaviorDetailsInFlight: UInt32?
    private var behaviorDetailsTimeoutWorkItem: DispatchWorkItem?

    // Connection lifecycle state.
    private var isConnecting = false
    private var reconnectWorkItem: DispatchWorkItem?

    // Persist the last compatible keyboard so reconnect does not depend on
    // the keyboard advertising a particular service UUID.
    private var knownPeripheralID: UUID? {
        get {
            let defaults = UserDefaults.standard

            if let raw = defaults.string(
                forKey: "ZMKOverlayPeripheralIdentifier"
            ) {
                return UUID(uuidString: raw)
            }

            // One-time migration from the original TOTEM-only build.
            if let legacy = defaults.string(
                forKey: "TOTEMPeripheralIdentifier"
            ),
               let identifier = UUID(uuidString: legacy) {

                defaults.set(
                    identifier.uuidString,
                    forKey: "ZMKOverlayPeripheralIdentifier"
                )

                return identifier
            }

            return nil
        }

        set {
            let defaults = UserDefaults.standard

            if let newValue {
                defaults.set(
                    newValue.uuidString,
                    forKey: "ZMKOverlayPeripheralIdentifier"
                )
            } else {
                defaults.removeObject(
                    forKey: "ZMKOverlayPeripheralIdentifier"
                )
            }
        }
    }

    // MARK: - Local overlay cache

    private struct CachedPhysicalKey: Codable {
        let id: Int
        let x: Double
        let y: Double
        let width: Double
        let height: Double
        let rotation: Double
    }

    private struct OverlayCache: Codable {
        let schemaVersion: Int
        let peripheralID: String
        let layerIDs: [Int]
        let layerNames: [String]
        let layerLabels: [[String]]
        let layerHoldModifierMasks: [[UInt8]]
        let layerHoldModifierLabels: [[String]]
        let physicalKeys: [CachedPhysicalKey]
    }

    private let overlayCacheSchemaVersion = 1
    private var loadedCachePeripheralID: UUID?

    private func cacheURL(
        for peripheralID: UUID
    ) -> URL? {
        guard let applicationSupport =
            FileManager.default.urls(
                for: .applicationSupportDirectory,
                in: .userDomainMask
            ).first
        else {
            return nil
        }

        let directory =
            applicationSupport
                .appendingPathComponent(
                    "ZMK Overlay",
                    isDirectory: true
                )
                .appendingPathComponent(
                    "Keyboard Cache",
                    isDirectory: true
                )

        do {
            try FileManager.default.createDirectory(
                at: directory,
                withIntermediateDirectories: true
            )
        } catch {
            print(
                "Failed to create overlay cache directory:",
                error
            )
            return nil
        }

        return directory.appendingPathComponent(
            "\(peripheralID.uuidString).json"
        )
    }


    private func loadOverlayCache(
        for peripheralID: UUID
    ) {
        guard loadedCachePeripheralID != peripheralID else {
            return
        }

        loadedCachePeripheralID = peripheralID

        guard let url = cacheURL(for: peripheralID) else {
            return
        }

        guard FileManager.default.fileExists(
            atPath: url.path
        ) else {
            hasCachedOverlay = false
            print(
                "No cached overlay for:",
                peripheralID
            )
            return
        }

        do {
            let data = try Data(
                contentsOf: url
            )

            let cache = try JSONDecoder().decode(
                OverlayCache.self,
                from: data
            )

            guard
                cache.schemaVersion ==
                    overlayCacheSchemaVersion,
                cache.peripheralID ==
                    peripheralID.uuidString
            else {
                print(
                    "Ignoring incompatible overlay cache"
                )
                hasCachedOverlay = false
                return
            }

            let keys = cache.physicalKeys.map {
                KeyDisplay(
                    id: $0.id,
                    label: "",
                    x: CGFloat($0.x),
                    y: CGFloat($0.y),
                    width: CGFloat($0.width),
                    height: CGFloat($0.height),
                    rotation: $0.rotation
                )
            }

            layerIDs = cache.layerIDs
            layerNames = cache.layerNames
            layerLabels = cache.layerLabels
            layerHoldModifierMasks =
                cache.layerHoldModifierMasks
            layerHoldModifierLabels =
                cache.layerHoldModifierLabels
            physicalKeys = keys

            hasCachedOverlay = true

            if let reportedID = lastReportedLayerID,
               let index = layerIDs.firstIndex(
                    of: reportedID
               ) {
                activeLayer = index
            } else if activeLayer >= layerLabels.count {
                activeLayer = 0
            }

            print(
                "Loaded cached overlay:",
                layerNames.count,
                "layers,",
                physicalKeys.count,
                "keys"
            )

        } catch {
            hasCachedOverlay = false

            print(
                "Failed to load overlay cache:",
                error
            )
        }
    }


    private func saveOverlayCache() {
        guard let peripheralID = knownPeripheralID else {
            print(
                "Cannot save overlay cache: keyboard ID unavailable"
            )
            return
        }

        guard
            !layerNames.isEmpty,
            !layerLabels.isEmpty,
            !physicalKeys.isEmpty
        else {
            print(
                "Cannot save overlay cache: metadata incomplete"
            )
            return
        }

        guard let url = cacheURL(for: peripheralID) else {
            return
        }

        let cachedKeys = physicalKeys.map {
            CachedPhysicalKey(
                id: $0.id,
                x: Double($0.x),
                y: Double($0.y),
                width: Double($0.width),
                height: Double($0.height),
                rotation: $0.rotation
            )
        }

        let cache = OverlayCache(
            schemaVersion: overlayCacheSchemaVersion,
            peripheralID: peripheralID.uuidString,
            layerIDs: layerIDs,
            layerNames: layerNames,
            layerLabels: layerLabels,
            layerHoldModifierMasks:
                layerHoldModifierMasks,
            layerHoldModifierLabels:
                layerHoldModifierLabels,
            physicalKeys: cachedKeys
        )

        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = [
                .prettyPrinted,
                .sortedKeys
            ]

            let data = try encoder.encode(cache)

            try data.write(
                to: url,
                options: .atomic
            )

            hasCachedOverlay = true
            loadedCachePeripheralID = peripheralID

            print(
                "Saved overlay cache:",
                url.path
            )

        } catch {
            print(
                "Failed to save overlay cache:",
                error
            )
        }
    }


    private func finishRefreshIfReady() {
        guard
            isRefreshingKeymap,
            refreshHasKeymap,
            refreshHasPhysicalLayout,
            refreshBehaviorsComplete,
            refreshLabelsReady
        else {
            return
        }

        saveOverlayCache()

        isRefreshingKeymap = false
        keymapCacheDirty = false

        // Anything arriving after this point belongs to an expired refresh
        // transaction and should not mutate the overlay.
        ownedRequestIDs.removeAll()

        status = "Keymap cache refreshed"

        print("Manual keymap refresh complete")
    }


    private func allocateRequestID() -> UInt32 {
        let requestID = nextRequestID

        nextRequestID &+= 1

        // Keep the overlay in the high half of the UInt32 request-ID space.
        if nextRequestID < 0x8000_0000 {
            nextRequestID = 0x8000_0000
        }

        ownedRequestIDs.insert(
            requestID
        )

        return requestID
    }



    override init() {
        super.init()

        print("Creating CBCentralManager")
        print("Bluetooth authorization:", CBManager.authorization.rawValue)

        frameCodec.onFrame = { [weak self] data in
            self?.handleRPCFrame(data)
        }

        central = CBCentralManager(
            delegate: self,
            queue: nil
        )

        // Rendering metadata comes from the last successful local cache.
        // Studio RPC is not queried automatically.
        if let identifier = knownPeripheralID {
            loadOverlayCache(
                for: identifier
            )
        }
    }


    // MARK: - Connection lifecycle

    private func resetFrameCodec() {
        frameCodec = FrameCodec()

        frameCodec.onFrame = { [weak self] data in
            self?.handleRPCFrame(data)
        }
    }


    private func resetConnectionSession() {
        studioCharacteristic = nil
        layerCharacteristic = nil
        keyEventCharacteristic = nil
        protocolInfoCharacteristic = nil
        modifierStateCharacteristic = nil

        DispatchQueue.main.async { [weak self] in
            self?.pressedKeys.removeAll()
            self?.resolvedModifierHoldPositions.removeAll()
            self?.activeModifiers = 0
            self?.pressSequenceByPosition.removeAll()
            self?.companionProtocolVersion = nil
            self?.companionCapabilities = 0
        }

        pendingBehaviorIDs.removeAll()
        nextRequestID = 0x8000_0000
        ownedRequestIDs.removeAll()

        refreshHasKeymap = false
        refreshHasPhysicalLayout = false
        refreshBehaviorsComplete = false
        refreshLabelsReady = false
        isRefreshingKeymap = false

        behaviorDetailsTimeoutWorkItem?.cancel()
        behaviorDetailsTimeoutWorkItem = nil
        behaviorDetailsInFlight = nil


        resetFrameCodec()
    }


    private func beginConnectionDiscovery() {
        guard central.state == .poweredOn else {
            status = "Bluetooth unavailable"
            return
        }

        guard !isConnecting else {
            return
        }

        reconnectWorkItem?.cancel()
        reconnectWorkItem = nil

        central.stopScan()

        /*
         * Best reconnect path:
         *
         * If this app already has a CBPeripheral object, reconnect directly
         * to it. CoreBluetooth keeps the connection request pending until the
         * peripheral becomes available again.
         */
        if let device = peripheral {
            connectToPeripheral(device)
            return
        }

        /*
         * If the app was restarted, retrieve the previously known peripheral
         * by CoreBluetooth's stable identifier and reconnect directly.
         */
        if let identifier = knownPeripheralID {
            let known = central.retrievePeripherals(
                withIdentifiers: [identifier]
            )

            if let device = known.first {
                print(
                    "Retrieved known ZMK keyboard:",
                    device.identifier
                )

                connectToPeripheral(device)
                return
            }
        }

        /*
         * Next, check whether macOS already has the keyboard connected as a
         * system Bluetooth device.
         */
        let connected = central.retrieveConnectedPeripherals(
            withServices: [serviceUUID]
        )

        if let device = connected.first {
            connectToPeripheral(device)
            return
        }

        /*
         * Last resort for first discovery. Normally a paired keyboard is
         * already connected to macOS and is found above. The fallback scan
         * only considers devices advertising ZMK Studio or Overlay Companion.
         */
        status = "Searching for ZMK keyboard"
        print("Scanning for compatible ZMK keyboard...")

        central.scanForPeripherals(
            withServices: [
                serviceUUID,
                companionServiceUUID
            ],
            options: [
                CBCentralManagerScanOptionAllowDuplicatesKey: false
            ]
        )
    }


    private func connectToPeripheral(_ device: CBPeripheral) {
        guard central.state == .poweredOn else {
            return
        }

        if device.state == .connected {
            /*
             * It may already be connected at the CoreBluetooth level.
             * Treat it like a normal didConnect and rediscover our services.
             */
            central.stopScan()

            peripheral = device
            device.delegate = self
            knownPeripheralID = device.identifier
            connectedDeviceName =
                device.name ?? "ZMK Keyboard"

            loadOverlayCache(
                for: device.identifier
            )

            isConnecting = false
            resetConnectionSession()

            status = "Connected"

            print(
                "ZMK keyboard already connected:",
                device.name ?? "Unknown"
            )

            device.discoverServices([
                serviceUUID,
                companionServiceUUID
            ])

            return
        }

        if device.state == .connecting || isConnecting {
            return
        }

        central.stopScan()

        peripheral = device
        device.delegate = self
        knownPeripheralID = device.identifier

        isConnecting = true
        status = "Connecting"

        print(
            "Connecting to:",
            device.name ?? "Unknown",
            device.identifier
        )

        /*
         * CoreBluetooth connection requests remain pending. If the dongle is
         * currently powered off, this request can complete when it powers on.
         */
        central.connect(
            device,
            options: nil
        )
    }


    private func scheduleReconnect(after delay: TimeInterval = 0.5) {
        guard central.state == .poweredOn else {
            return
        }

        reconnectWorkItem?.cancel()

        let workItem = DispatchWorkItem { [weak self] in
            guard let self else { return }

            self.isConnecting = false
            self.beginConnectionDiscovery()
        }

        reconnectWorkItem = workItem

        DispatchQueue.main.asyncAfter(
            deadline: .now() + delay,
            execute: workItem
        )
    }

    // MARK: - RPC response handling

    private func handleRPCFrame(_ data: Data) {
        do {
            let response = try Zmk_Studio_Response(
                serializedBytes: data
            )

            switch response.type {

            case .requestResponse(let requestResponse):
                let requestID =
                    requestResponse.requestID

                guard ownedRequestIDs.remove(
                    requestID
                ) != nil else {
                    print(
                        "Ignoring Studio RPC response " +
                        "not owned by overlay:",
                        requestID
                    )
                    return
                }

                switch requestResponse.subsystem {

                case .keymap(let keymapResponse):
                    handleKeymapResponse(keymapResponse)

                case .behaviors(let behaviorsResponse):
                    handleBehaviorsResponse(behaviorsResponse)

                case .core:
                    break

                case .meta:
                    break

                case nil:
                    break
                }

            case .notification(let notification):
                handleNotification(notification)

            case nil:
                break
            }

        } catch {
            print("Failed to decode protobuf:", error)
        }
    }


    private func handleNotification(
        _ notification: Zmk_Studio_Notification
    ) {
        switch notification.subsystem {

        case .keymap:
            keymapCacheDirty = true

            print(
                "Keymap changed — local cache marked stale"
            )

        case .core:
            break

        case nil:
            break
        }
    }


    private func handleKeymapResponse(
        _ response: Zmk_Keymap_Response
    ) {
        switch response.responseType {

        case .getKeymap(let keymap):
            currentKeymap = keymap

            if isRefreshingKeymap {
                refreshHasKeymap = true
            }

            print("\nKEYMAP:")

            for layer in keymap.layers {
                print(
                    "Layer \(layer.id): \(layer.name) - \(layer.bindings.count) keys"
                )
            }

            if !behaviorNames.isEmpty {
                rebuildLayerLabels()
            }

        case .getPhysicalLayouts(let layouts):
            handlePhysicalLayouts(layouts)

        case nil:
            print("Keymap response has no response type")

        default:
            print("Received other keymap response")
        }
    }


    private func handlePhysicalLayouts(
        _ layouts: Zmk_Keymap_PhysicalLayouts
    ) {
        let index = Int(layouts.activeLayoutIndex)

        guard index >= 0,
              index < layouts.layouts.count else {
            print("Invalid physical layout index:", index)
            return
        }

        let layout = layouts.layouts[index]

        print(
            "Physical layout:",
            layout.name,
            "- \(layout.keys.count) keys"
        )

        struct TempKey {
            let id: Int
            let centerX: CGFloat
            let centerY: CGFloat
            let width: CGFloat
            let height: CGFloat
            let rotation: Double
            let corners: [(CGFloat, CGFloat)]
        }

        func rotate(
            x: CGFloat,
            y: CGFloat,
            aroundX rx: CGFloat,
            aroundY ry: CGFloat,
            degrees: Double
        ) -> (CGFloat, CGFloat) {

            let radians = CGFloat(degrees * .pi / 180.0)

            let dx = x - rx
            let dy = y - ry

            let newX =
                rx +
                dx * cos(radians) -
                dy * sin(radians)

            let newY =
                ry +
                dx * sin(radians) +
                dy * cos(radians)

            return (newX, newY)
        }

        var tempKeys: [TempKey] = []

        for (keyIndex, attrs) in layout.keys.enumerated() {

            // ZMK physical layout values are centi-keyunits.
            let w = CGFloat(attrs.width) / 100.0
            let h = CGFloat(attrs.height) / 100.0

            let x = CGFloat(attrs.x) / 100.0
            let y = CGFloat(attrs.y) / 100.0

            let rotation = Double(attrs.r) / 100.0

            let rx = CGFloat(attrs.rx) / 100.0
            let ry = CGFloat(attrs.ry) / 100.0

            let rawCenterX = x + w / 2.0
            let rawCenterY = y + h / 2.0

            let center = rotate(
                x: rawCenterX,
                y: rawCenterY,
                aroundX: rx,
                aroundY: ry,
                degrees: rotation
            )

            let rawCorners = [
                (x, y),
                (x + w, y),
                (x, y + h),
                (x + w, y + h)
            ]

            let corners = rawCorners.map {
                rotate(
                    x: $0.0,
                    y: $0.1,
                    aroundX: rx,
                    aroundY: ry,
                    degrees: rotation
                )
            }

            tempKeys.append(
                TempKey(
                    id: keyIndex,
                    centerX: center.0,
                    centerY: center.1,
                    width: w,
                    height: h,
                    rotation: rotation,
                    corners: corners
                )
            )
        }

        let allCorners = tempKeys.flatMap { $0.corners }

        guard
            let minX = allCorners.map({ $0.0 }).min(),
            let maxX = allCorners.map({ $0.0 }).max(),
            let minY = allCorners.map({ $0.1 }).min(),
            let maxY = allCorners.map({ $0.1 }).max()
        else {
            print("Unable to calculate physical layout bounds")
            return
        }

        let layoutWidth = maxX - minX
        let layoutHeight = maxY - minY

        // Matches the current 900 × 330 keyboard drawing area.
        let availableWidth: CGFloat = 860
        let availableHeight: CGFloat = 290
        let padding: CGFloat = 20

        let scaleX = availableWidth / layoutWidth
        let scaleY = availableHeight / layoutHeight
        let scale = min(scaleX, scaleY)

        print(
            "Layout bounds:",
            "width=\(layoutWidth)",
            "height=\(layoutHeight)",
            "scale=\(scale)"
        )

        let keys: [KeyDisplay] = tempKeys.map { key in
            KeyDisplay(
                id: key.id,
                label: "",
                x: padding + (key.centerX - minX) * scale,
                y: padding + (key.centerY - minY) * scale,
                width: key.width * scale,
                height: key.height * scale,
                rotation: key.rotation
            )
        }

        DispatchQueue.main.async { [weak self] in
            guard let self else { return }

            self.physicalKeys = keys

            if self.isRefreshingKeymap {
                self.refreshHasPhysicalLayout = true
                self.finishRefreshIfReady()
            }

            print("Published \(keys.count) physical keys")
        }
    }


    private func handleBehaviorsResponse(
        _ response: Zmk_Behaviors_Response
    ) {
        switch response.responseType {

        case .listAllBehaviors(let list):
            behaviorDetailsTimeoutWorkItem?.cancel()
            behaviorDetailsTimeoutWorkItem = nil
            behaviorDetailsInFlight = nil

            pendingBehaviorIDs = list.behaviors
            behaviorNames.removeAll()

            print(
                "\nReceived \(pendingBehaviorIDs.count) behavior IDs:",
                pendingBehaviorIDs
            )

            requestNextBehaviorDetails()

        case .getBehaviorDetails(let details):
            let behaviorID = details.id

            behaviorNames[behaviorID] = details.displayName

            print(
                "Behavior \(behaviorID): \(details.displayName)"
            )

            /*
             * If this is the request we were waiting for, advance the
             * sequential loader. If it is a late response from a behavior
             * we already timed out and skipped, keep the metadata but do not
             * disturb the current in-flight request.
             */
            if behaviorDetailsInFlight == behaviorID {
                behaviorDetailsTimeoutWorkItem?.cancel()
                behaviorDetailsTimeoutWorkItem = nil
                behaviorDetailsInFlight = nil

                // Labels can become useful before every behavior has loaded.
                rebuildLayerLabels()

                requestNextBehaviorDetails()
            } else {
                // Late response: still improve the labels with it.
                rebuildLayerLabels()
            }

        case nil:
            print("Behavior response has no response type")
        }
    }


    // MARK: - Layer label decoding

    private struct ResolvedBinding {
        let behaviorID: UInt32
        let param1: UInt32
        let param2: UInt32
    }


    private func rebuildLayerLabels() {
        guard let keymap = currentKeymap else {
            print("Cannot build layer labels: keymap not loaded yet")
            return
        }

        guard !behaviorNames.isEmpty else {
            print("Cannot build layer labels: behavior metadata not loaded yet")
            return
        }

        var ids: [Int] = []
        var names: [String] = []
        var allLabels: [[String]] = []
        var allHoldModifierMasks: [[UInt8]] = []
        var allHoldModifierLabels: [[String]] = []

        for (layerIndex, layer) in keymap.layers.enumerated() {
            ids.append(Int(layer.id))
            names.append(layer.name)

            var labels: [String] = []
            var holdModifierMasks: [UInt8] = []
            var holdModifierLabels: [String] = []

            for keyIndex in layer.bindings.indices {
                guard let binding = effectiveBinding(
                    at: keyIndex,
                    on: layerIndex,
                    in: keymap
                ) else {
                    labels.append("")
                    holdModifierMasks.append(0)
                    holdModifierLabels.append("")
                    continue
                }

                labels.append(
                    labelForBinding(
                        binding,
                        in: keymap
                    )
                )

                let modifierMask =
                    holdModifierMaskForBinding(binding)

                holdModifierMasks.append(
                    modifierMask
                )

                holdModifierLabels.append(
                    modifierMask == 0
                        ? ""
                        : HIDKeyLabel.label(
                            for: binding.param1
                        )
                )
            }

            allLabels.append(labels)
            allHoldModifierMasks.append(holdModifierMasks)
            allHoldModifierLabels.append(holdModifierLabels)
        }

        DispatchQueue.main.async { [weak self] in
            guard let self else { return }

            self.layerIDs = ids
            self.layerNames = names
            self.layerLabels = allLabels
            self.layerHoldModifierMasks = allHoldModifierMasks
            self.layerHoldModifierLabels = allHoldModifierLabels

            if self.isRefreshingKeymap {
                self.refreshLabelsReady = true
            }

            if let reportedID = self.lastReportedLayerID,
               let index = ids.firstIndex(of: reportedID) {
                self.activeLayer = index
            } else if self.activeLayer >= allLabels.count {
                self.activeLayer = 0
            }

            print(
                "Published \(allLabels.count) layers:",
                names.joined(separator: ", ")
            )

            if self.isRefreshingKeymap {
                self.finishRefreshIfReady()
            }
        }
    }


    private func effectiveBinding(
        at keyIndex: Int,
        on layerIndex: Int,
        in keymap: Zmk_Keymap_Keymap
    ) -> ResolvedBinding? {
        var index = layerIndex

        while index >= 0 {
            let layer = keymap.layers[index]

            guard keyIndex < layer.bindings.count else {
                return nil
            }

            let binding = layer.bindings[keyIndex]

            let behaviorID = UInt32(binding.behaviorID)
            let behaviorName =
                behaviorNames[behaviorID] ?? "Unknown"

            if behaviorName != "Transparent" {
                return ResolvedBinding(
                    behaviorID: behaviorID,
                    param1: UInt32(binding.param1),
                    param2: UInt32(binding.param2)
                )
            }

            index -= 1
        }

        return nil
    }


    /*
     * ZMK encodes HID usage page in bits 16-23 and usage ID in bits 0-15.
     * Keyboard modifiers occupy usages 0xE0...0xE7.
     */
    private func modifierMask(
        forEncodedHID encoded: UInt32
    ) -> UInt8 {
        var usagePage =
            UInt8((encoded >> 16) & 0xFF)

        let usageID =
            UInt16(encoded & 0xFFFF)

        // ZMK treats a zero page as the keyboard usage page.
        if usagePage == 0 {
            usagePage = 0x07
        }

        guard
            usagePage == 0x07,
            usageID >= 0xE0,
            usageID <= 0xE7
        else {
            return 0
        }

        let bitIndex =
            Int(usageID - 0xE0)

        return UInt8(
            1 << bitIndex
        )
    }


    /*
     * Standard &mt and custom hold-taps both arrive as two-parameter
     * behaviors. If param1 is a modifier HID usage and param2 is populated,
     * treat it as a possible modifier-hold key.
     *
     * This intentionally does not depend on a display name such as
     * "Mod-Tap" or "Home Row Mod Left", so custom HRM behavior names work too.
     */
    private func holdModifierMaskForBinding(
        _ binding: ResolvedBinding
    ) -> UInt8 {
        guard binding.param2 != 0 else {
            return 0
        }

        return modifierMask(
            forEncodedHID: binding.param1
        )
    }


    func holdModifierMask(
        at position: Int
    ) -> UInt8 {
        guard
            activeLayer >= 0,
            activeLayer < layerHoldModifierMasks.count,
            position >= 0,
            position < layerHoldModifierMasks[activeLayer].count
        else {
            return 0
        }

        return layerHoldModifierMasks[activeLayer][position]
    }


    func holdModifierLabel(
        at position: Int
    ) -> String {
        guard
            activeLayer >= 0,
            activeLayer < layerHoldModifierLabels.count,
            position >= 0,
            position < layerHoldModifierLabels[activeLayer].count
        else {
            return ""
        }

        return layerHoldModifierLabels[activeLayer][position]
    }


    func isResolvedModifierHold(
        at position: Int
    ) -> Bool {
        pressedKeys.contains(position) &&
        resolvedModifierHoldPositions.contains(position)
    }


    private func handleModifierStateEvent(
        currentMask: UInt8,
        eventMask: UInt8,
        isPressed: Bool
    ) {
        activeModifiers = currentMask

        guard
            isPressed,
            eventMask != 0
        else {
            return
        }

        /*
         * A modifier keycode event only occurs when ZMK actually activates
         * that modifier. Match it to the most recently pressed, unresolved
         * two-parameter hold-tap whose hold parameter is the same modifier.
         *
         * This lets the UI distinguish:
         *   physical down / undecided
         * from
         *   hold side actually resolved.
         */
        let candidates =
            pressedKeys.filter { position in
                !resolvedModifierHoldPositions.contains(position) &&
                holdModifierMask(at: position) == eventMask
            }

        guard
            let resolvedPosition = candidates.max(
                by: { left, right in
                    let leftOrder =
                        pressSequenceByPosition[left] ?? 0

                    let rightOrder =
                        pressSequenceByPosition[right] ?? 0

                    return leftOrder < rightOrder
                }
            )
        else {
            return
        }

        resolvedModifierHoldPositions.insert(
            resolvedPosition
        )

        print(
            "Modifier hold resolved:",
            resolvedPosition,
            holdModifierLabel(at: resolvedPosition)
        )
    }


    private func labelForBinding(
        _ binding: ResolvedBinding,
        in keymap: Zmk_Keymap_Keymap
    ) -> String {
        let behaviorName =
            behaviorNames[binding.behaviorID] ?? "Unknown"

        switch behaviorName {

        case "Unknown":
            /*
             * Custom two-parameter hold-taps (such as hml/hmr) can still be
             * rendered even if Studio does not return metadata for them.
             */
            if binding.param1 != 0 && binding.param2 != 0 {
                let hold = HIDKeyLabel.label(
                    for: binding.param1
                )

                let tap = HIDKeyLabel.label(
                    for: binding.param2
                )

                return "\(hold)/\(tap)"
            }

            return "Unknown"

        case "Key Press":
            return HIDKeyLabel.label(
                for: binding.param1
            )

        case "Mod-Tap",
             "Home Row Mod Left",
             "Home Row Mod Right":

            let hold = HIDKeyLabel.label(
                for: binding.param1
            )

            let tap = HIDKeyLabel.label(
                for: binding.param2
            )

            return "\(hold)/\(tap)"

        case "Layer-Tap":
            let layerID = Int(binding.param1)

            let layerName =
                keymap.layers
                    .first(where: { Int($0.id) == layerID })?
                    .name
                ?? "L\(layerID)?"

            let tap = HIDKeyLabel.label(
                for: binding.param2
            )

            return "\(layerName)/\(tap)"

        case "Momentary Layer",
             "Sticky Layer",
             "To Layer",
             "Toggle Layer":
            let layerID = Int(binding.param1)

            return
                keymap.layers
                    .first(where: { Int($0.id) == layerID })?
                    .name
                ?? "L\(layerID)?"

        default:
            return behaviorName
        }
    }

    // MARK: - Manual Studio metadata refresh

    @discardableResult
    func refreshKeymap() -> Bool {
        guard
            peripheral != nil,
            studioCharacteristic != nil
        else {
            status = "Studio RPC unavailable"

            print(
                "Cannot refresh keymap: " +
                "Studio BLE characteristic is not ready"
            )
            return false
        }

        guard !isRefreshingKeymap else {
            print("Keymap refresh already in progress")
            return false
        }

        isRefreshingKeymap = true
        status = "Refreshing keymap cache"

        refreshHasKeymap = false
        refreshHasPhysicalLayout = false
        refreshBehaviorsComplete = false
        refreshLabelsReady = false

        currentKeymap = nil
        behaviorNames.removeAll()
        pendingBehaviorIDs.removeAll()

        behaviorDetailsTimeoutWorkItem?.cancel()
        behaviorDetailsTimeoutWorkItem = nil
        behaviorDetailsInFlight = nil

        ownedRequestIDs.removeAll()
        nextRequestID = 0x8000_0000

        print("Starting manual keymap refresh")

        sendGetKeymap()
        sendListBehaviors()
        sendGetPhysicalLayouts()

        return true
    }


    // MARK: - BLE write

    func send(_ data: Data) {
        guard
            let peripheral,
            let characteristic = studioCharacteristic
        else {
            print("Studio BLE characteristic not ready")
            return
        }

        peripheral.writeValue(
            data,
            for: characteristic,
            type: .withResponse
        )
    }


    // MARK: - ZMK Studio requests

    func sendGetKeymap() {
        do {
            var keymapRequest = Zmk_Keymap_Request()
            keymapRequest.requestType = .getKeymap(true)

            var request = Zmk_Studio_Request()
            request.requestID = allocateRequestID()
            request.subsystem = .keymap(keymapRequest)

            let protobuf = try request.serializedData()
            let framed = FrameCodec.encode(protobuf)

            print(
                "TX:",
                framed.map {
                    String(format: "%02X", $0)
                }.joined(separator: " ")
            )

            send(framed)

        } catch {
            print("Failed to encode request:", error)
        }
    }


    func sendListBehaviors() {
        do {
            var behaviorRequest = Zmk_Behaviors_Request()
            behaviorRequest.requestType = .listAllBehaviors(true)

            var request = Zmk_Studio_Request()
            request.requestID = allocateRequestID()
            request.subsystem = .behaviors(behaviorRequest)

            let protobuf = try request.serializedData()
            let framed = FrameCodec.encode(protobuf)

            print("Requesting behavior list...")
            send(framed)

        } catch {
            print("Failed to encode behavior request:", error)
        }
    }


    func sendGetPhysicalLayouts() {
        do {
            var keymapRequest = Zmk_Keymap_Request()
            keymapRequest.requestType = .getPhysicalLayouts(true)

            var request = Zmk_Studio_Request()
            request.requestID = allocateRequestID()
            request.subsystem = .keymap(keymapRequest)

            let protobuf = try request.serializedData()
            let framed = FrameCodec.encode(protobuf)

            print("Requesting physical layout...")
            send(framed)

        } catch {
            print("Failed to request physical layout:", error)
        }
    }


    private func requestNextBehaviorDetails() {
        // Only one details request may be active at a time.
        guard behaviorDetailsInFlight == nil else {
            return
        }

        guard !pendingBehaviorIDs.isEmpty else {
            behaviorDetailsTimeoutWorkItem?.cancel()
            behaviorDetailsTimeoutWorkItem = nil

            print("\nBEHAVIOR MAP:")

            for id in behaviorNames.keys.sorted() {
                if let name = behaviorNames[id] {
                    print("\(id): \(name)")
                }
            }

            print(
                "\nLoaded \(behaviorNames.count) behavior names."
            )

            if isRefreshingKeymap {
                refreshBehaviorsComplete = true
            }

            rebuildLayerLabels()
            finishRefreshIfReady()
            return
        }

        let behaviorID = pendingBehaviorIDs.removeFirst()
        let requestID = allocateRequestID()

        behaviorDetailsInFlight = behaviorID

        do {
            var details = Zmk_Behaviors_GetBehaviorDetailsRequest()
            details.behaviorID = behaviorID

            var behaviorRequest = Zmk_Behaviors_Request()
            behaviorRequest.requestType = .getBehaviorDetails(details)

            var request = Zmk_Studio_Request()
            request.requestID = requestID
            request.subsystem = .behaviors(behaviorRequest)

            let protobuf = try request.serializedData()
            let framed = FrameCodec.encode(protobuf)

            print("Requesting behavior details:", behaviorID)
            send(framed)

            /*
             * A custom behavior can appear in listAllBehaviors but fail to
             * produce a details response. Do not let one such behavior block
             * the entire overlay.
             */
            let timeout = DispatchWorkItem { [weak self] in
                guard let self else { return }

                guard self.behaviorDetailsInFlight == behaviorID else {
                    return
                }

                print(
                    "Behavior \(behaviorID) details timed out — skipping"
                )

                self.behaviorDetailsInFlight = nil
                self.behaviorDetailsTimeoutWorkItem = nil

                // Publish whatever metadata we have so far.
                self.rebuildLayerLabels()

                self.requestNextBehaviorDetails()
            }

            behaviorDetailsTimeoutWorkItem = timeout

            DispatchQueue.main.asyncAfter(
                deadline: .now() + 0.5,
                execute: timeout
            )

        } catch {
            print(
                "Failed to request behavior \(behaviorID):",
                error
            )

            behaviorDetailsInFlight = nil
            behaviorDetailsTimeoutWorkItem?.cancel()
            behaviorDetailsTimeoutWorkItem = nil

            requestNextBehaviorDetails()
        }
    }


    // MARK: - Active layer handling

    private func handleReportedLayerID(_ layerID: Int) {
        lastReportedLayerID = layerID

        DispatchQueue.main.async { [weak self] in
            guard let self else { return }

            guard let index = self.layerIDs.firstIndex(of: layerID) else {
                print(
                    "Received active layer ID \(layerID), " +
                    "but the runtime keymap does not contain it yet"
                )
                return
            }

            self.activeLayer = index

            if index < self.layerNames.count {
                print(
                    "Overlay layer:",
                    self.layerNames[index]
                )
            }
        }
    }
}


// MARK: - CBCentralManagerDelegate

extension BLETransport: CBCentralManagerDelegate {

    func centralManagerDidUpdateState(
        _ central: CBCentralManager
    ) {
        print("Bluetooth state:", central.state.rawValue)
        print(
            "Bluetooth authorization:",
            CBManager.authorization.rawValue
        )

        guard central.state == .poweredOn else {
            reconnectWorkItem?.cancel()
            reconnectWorkItem = nil

            central.stopScan()

            isConnecting = false
            status = "Bluetooth unavailable"
            return
        }

        beginConnectionDiscovery()
    }


    func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String : Any],
        rssi RSSI: NSNumber
    ) {
        print(
            "Found compatible ZMK keyboard:",
            peripheral.name ?? "Unknown",
            peripheral.identifier,
            "RSSI:",
            RSSI
        )

        connectToPeripheral(peripheral)
    }


    func centralManager(
        _ central: CBCentralManager,
        didConnect peripheral: CBPeripheral
    ) {
        print(
            "CoreBluetooth connected to:",
            peripheral.name ?? "Unknown",
            peripheral.identifier
        )

        reconnectWorkItem?.cancel()
        reconnectWorkItem = nil

        isConnecting = false

        self.peripheral = peripheral
        self.knownPeripheralID = peripheral.identifier
        self.connectedDeviceName =
            peripheral.name ?? "ZMK Keyboard"

        loadOverlayCache(
            for: peripheral.identifier
        )

        peripheral.delegate = self

        resetConnectionSession()

        status = "Connected"

        peripheral.discoverServices([
            serviceUUID,
            companionServiceUUID
        ])
    }


    func centralManager(
        _ central: CBCentralManager,
        didFailToConnect peripheral: CBPeripheral,
        error: Error?
    ) {
        print(
            "Failed to connect to \(peripheral.name ?? "Unknown"):",
            error?.localizedDescription ?? "Unknown error"
        )

        isConnecting = false

        // Keep the peripheral reference and identifier. Retrying a known
        // peripheral is more reliable than depending on advertisements.
        self.peripheral = peripheral
        self.knownPeripheralID = peripheral.identifier

        resetConnectionSession()

        status = "Disconnected"
        scheduleReconnect()
    }


    func centralManager(
        _ central: CBCentralManager,
        didDisconnectPeripheral peripheral: CBPeripheral,
        error: Error?
    ) {
        print(
            "Disconnected from \(peripheral.name ?? "Unknown"):",
            error?.localizedDescription ?? "No error"
        )

        isConnecting = false

        // IMPORTANT: keep this CBPeripheral. CoreBluetooth can reconnect
        // directly to the same known peripheral after the dongle powers up.
        self.peripheral = peripheral
        self.knownPeripheralID = peripheral.identifier

        resetConnectionSession()

        status = "Disconnected"

        /*
         * Re-issue connect shortly after the disconnect. Because CoreBluetooth
         * connection attempts do not time out, it can remain pending while
         * the dongle is powered off and complete when the dongle returns.
         */
        scheduleReconnect()
    }

}


// MARK: - CBPeripheralDelegate

extension BLETransport: CBPeripheralDelegate {

    func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverServices error: Error?
    ) {
        if let error {
            print(
                "Service discovery error:",
                error
            )
            return
        }

        guard let services = peripheral.services else {
            return
        }

        for service in services {

            if service.uuid == serviceUUID {
                peripheral.discoverCharacteristics(
                    [characteristicUUID],
                    for: service
                )
            }

            if service.uuid == companionServiceUUID {
                print("ZMK Overlay Companion service found")

                peripheral.discoverCharacteristics(
                    [
                        layerCharacteristicUUID,
                        keyEventCharacteristicUUID,
                        protocolInfoCharacteristicUUID,
                        modifierStateCharacteristicUUID
                    ],
                    for: service
                )
            }
        }
    }


    func peripheral(
        _ peripheral: CBPeripheral,
        didDiscoverCharacteristicsFor service: CBService,
        error: Error?
    ) {
        if let error {
            print(
                "Characteristic discovery error:",
                error
            )
            return
        }

        guard let characteristics = service.characteristics else {
            return
        }

        for characteristic in characteristics {

            if characteristic.uuid == characteristicUUID {
                studioCharacteristic = characteristic

                peripheral.setNotifyValue(
                    true,
                    for: characteristic
                )
            }

            if characteristic.uuid == layerCharacteristicUUID {
                print("Layer-state characteristic found")

                layerCharacteristic = characteristic

                // Subscribe to future layer changes.
                peripheral.setNotifyValue(
                    true,
                    for: characteristic
                )

                // Also read the currently active layer immediately.
                peripheral.readValue(
                    for: characteristic
                )
            }

            if characteristic.uuid == keyEventCharacteristicUUID {
                print("Key-event characteristic found")

                keyEventCharacteristic = characteristic

                peripheral.setNotifyValue(
                    true,
                    for: characteristic
                )
            }


            if characteristic.uuid == protocolInfoCharacteristicUUID {
                print("Overlay protocol-info characteristic found")

                protocolInfoCharacteristic = characteristic

                peripheral.readValue(
                    for: characteristic
                )
            }


            if characteristic.uuid == modifierStateCharacteristicUUID {
                print("Modifier-state characteristic found")

                modifierStateCharacteristic = characteristic

                peripheral.setNotifyValue(
                    true,
                    for: characteristic
                )

                // Get the current explicit modifier state immediately.
                peripheral.readValue(
                    for: characteristic
                )
            }
        }
    }


    func peripheral(
        _ peripheral: CBPeripheral,
        didUpdateNotificationStateFor characteristic: CBCharacteristic,
        error: Error?
    ) {
        if let error {
            print(
                "Notification setup error for \(characteristic.uuid):",
                error
            )
            return
        }

        if characteristic.uuid == characteristicUUID {
            guard characteristic.isNotifying else {
                print("Studio indications not enabled")
                return
            }

            status = hasCachedOverlay
                ? "Overlay ready"
                : "Ready — refresh keymap"

            print(
                "ZMK Studio characteristic ready " +
                "(manual refresh only)"
            )

            return
        }

        if characteristic.uuid == layerCharacteristicUUID {
            guard characteristic.isNotifying else {
                print("Layer-state notifications not enabled")
                return
            }

            print("Layer-state notifications ready")
        }


        if characteristic.uuid == keyEventCharacteristicUUID {
            guard characteristic.isNotifying else {
                print("Key-event notifications not enabled")
                return
            }

            print("Key-event notifications ready")
        }


        if characteristic.uuid == modifierStateCharacteristicUUID {
            guard characteristic.isNotifying else {
                print("Modifier-state notifications not enabled")
                return
            }

            print("Modifier-state notifications ready")
        }
    }


    func peripheral(
        _ peripheral: CBPeripheral,
        didUpdateValueFor characteristic: CBCharacteristic,
        error: Error?
    ) {
        if let error {
            print(
                "BLE value update error for \(characteristic.uuid):",
                error
            )
            return
        }

        guard let data = characteristic.value else {
            return
        }

        // Overlay Companion active-layer characteristic.
        if characteristic.uuid == layerCharacteristicUUID {
            let layerID: Int

            if data.count >= 2 {
                layerID =
                    Int(data[0]) |
                    (Int(data[1]) << 8)
            } else if let legacy = data.first {
                // Backward compatibility with the original one-byte firmware.
                layerID = Int(legacy)
            } else {
                return
            }

            print(
                "ACTIVE LAYER ID:",
                layerID
            )

            handleReportedLayerID(layerID)
            return
        }

        // Overlay Companion physical key press/release characteristic.
        if characteristic.uuid == keyEventCharacteristicUUID {
            let position: Int
            let isPressed: Bool

            if data.count >= 3 {
                position =
                    Int(data[0]) |
                    (Int(data[1]) << 8)

                isPressed = data[2] != 0
            } else if data.count >= 2 {
                // Backward compatibility with the original two-byte payload.
                position = Int(data[0])
                isPressed = data[1] != 0
            } else {
                print(
                    "Invalid key-event payload:",
                    data as NSData
                )
                return
            }

            DispatchQueue.main.async { [weak self] in
                guard let self else { return }

                if isPressed {
                    self.pressSequenceCounter += 1
                    self.pressSequenceByPosition[position] =
                        self.pressSequenceCounter

                    self.pressedKeys.insert(position)
                } else {
                    self.pressedKeys.remove(position)
                    self.resolvedModifierHoldPositions.remove(position)
                    self.pressSequenceByPosition.removeValue(
                        forKey: position
                    )
                }
            }

            return
        }

        // Overlay Companion protocol information.
        if characteristic.uuid == protocolInfoCharacteristicUUID {
            guard data.count >= 4 else {
                print(
                    "Invalid protocol-info payload:",
                    data as NSData
                )
                return
            }

            let major = Int(data[0])
            let minor = Int(data[1])

            let capabilities =
                UInt16(data[2]) |
                (UInt16(data[3]) << 8)

            DispatchQueue.main.async { [weak self] in
                self?.companionProtocolVersion =
                    "\(major).\(minor)"

                self?.companionCapabilities =
                    capabilities
            }

            print(
                "Overlay Companion protocol:",
                "\(major).\(minor)",
                "capabilities:",
                String(
                    format: "0x%04X",
                    capabilities
                )
            )

            return
        }

        // Overlay Companion explicit modifier state/event.
        if characteristic.uuid == modifierStateCharacteristicUUID {
            guard let currentMask = data.first else {
                return
            }

            let eventMask: UInt8 =
                data.count >= 2 ? data[1] : 0

            let isPressed =
                data.count >= 3 ? data[2] != 0 : false

            DispatchQueue.main.async { [weak self] in
                self?.handleModifierStateEvent(
                    currentMask: currentMask,
                    eventMask: eventMask,
                    isPressed: isPressed
                )
            }

            print(
                "ACTIVE MODIFIERS:",
                String(
                    format: "0x%02X",
                    currentMask
                ),
                "event:",
                String(
                    format: "0x%02X",
                    eventMask
                ),
                isPressed ? "pressed" : "released/read"
            )

            return
        }

        // Normal ZMK Studio RPC data.
        if characteristic.uuid == characteristicUUID {
            frameCodec.feed(data)
        }
    }
}
