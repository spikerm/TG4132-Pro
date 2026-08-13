import SwiftUI

@main
struct TR1604ProSimulatorApp: App {
    @StateObject private var model = InstrumentViewModel()

    var body: some Scene {
        WindowGroup {
            InstrumentScreen()
                .environmentObject(model)
                .preferredColorScheme(.dark)
        }
    }
}
