import Foundation
import ServiceManagement

@MainActor
final class LaunchAtLoginManager: ObservableObject {
    @Published private(set) var isEnabled = false
    @Published private(set) var errorMessage: String?

    private let service = SMAppService.mainApp

    init() {
        refreshStatus()
    }

    func setEnabled(_ enabled: Bool) {
        errorMessage = nil

        do {
            if enabled {
                try service.register()
            } else {
                try service.unregister()
            }

            refreshStatus()
        } catch {
            errorMessage = error.localizedDescription
            refreshStatus()
        }
    }

    func refreshStatus() {
        isEnabled = service.status == .enabled
    }
}
