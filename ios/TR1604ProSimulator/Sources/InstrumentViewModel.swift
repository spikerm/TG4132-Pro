import Foundation
import SwiftUI

@MainActor
final class InstrumentViewModel: ObservableObject {
    @Published var state = InstrumentSnapshot()
    @Published var sourceMode: DataSourceMode = .local
    @Published var menuVisible = true
    @Published var selectedMarker = 0
    @Published var menuIndex = 0
    @Published var menuFirst = 0
    @Published var memoryEnabled = false

    let firmware = "iOS 1.0.0"
    let core = "Instrument Core compatible"

    private let local = LocalSimulatorDataSource()
    private let usb = USBInstrumentDataSource()

    init() { refresh() }

    var menu: [String] {
        switch state.mode {
        case .spectrum:
            return ["TG ON/OFF", "TG LEVEL", "MARKER", "MARKER TO PEAK", "PEAK ZOOM", "UNZOOM", "START", "STOP", "SPAN", "RBW", "VBW", "TRACE MODE", "MEMORY", "DELTA ON/OFF", "AUTO TRACK", "REF LEVEL", "ATTENUATION", "SETUP"]
        case .duplex:
            return ["TG ON/OFF", "TG LEVEL", "MARKER", "SELECT NOTCH", "AUTO TRACK", "NOTCH ZOOM", "DELTA ON/OFF", "START", "STOP", "SPAN", "RBW", "VBW", "TRACE MODE", "BANDWIDTH", "Q FACTOR", "RIPPLE", "NOTCH DEPTH", "MEMORY", "SETUP"]
        case .antenna:
            return ["TG ON/OFF", "TG LEVEL", "MARKER", "AUTO TRACK", "MARKER TO MIN SWR", "SWR SCALE", "RETURN LOSS", "OPEN/SHORT/LOAD", "RBW", "VBW", "TRACE MODE", "MEMORY", "SETUP"]
        case .memory:
            return ["STORE TRACE", "MEMORY ON/OFF", "TRACE A/B", "A-B", "MAX HOLD", "MIN HOLD", "AVERAGE", "CLEAR TRACE", "MARKER", "DELTA ON/OFF", "SETUP"]
        case .loss:
            return ["TG ON/OFF", "TG LEVEL", "START", "STOP", "SPAN", "RBW", "VBW", "MARKER", "DELTA ON/OFF", "RIPPLE", "MEMORY", "SETUP"]
        case .setup:
            return ["DATA SOURCE", "DISPLAY INTENSITY", "CRT PERSISTENCE", "SERVICE INFORMATION", "ABOUT"]
        }
    }

    var visibleMenu: ArraySlice<String> {
        syncMenuWindow()
        let end = min(menu.count, menuFirst + 12)
        return menu[menuFirst..<end]
    }

    var menuPageText: String {
        let pages = max(1, Int(ceil(Double(menu.count) / 12.0)))
        let page = min(pages, menuFirst / 12 + 1)
        var hints: [String] = ["PAGE \(page)/\(pages)"]
        if menuFirst > 0 { hints.append("▲ MORE") }
        if menuFirst + 12 < menu.count { hints.append("▼ MORE") }
        return hints.joined(separator: "        ")
    }

    func refresh() {
        switch sourceMode {
        case .local: state = local.snapshot(from: state)
        case .usb: state = usb.snapshot(from: state)
        }
    }

    func setMode(_ mode: InstrumentMode) {
        state.mode = mode
        menuIndex = 0
        menuFirst = 0
        refresh()
    }

    func toggleMenu() { menuVisible.toggle() }

    func selectMenu(relative index: Int) {
        menuIndex = min(menu.count - 1, max(0, menuFirst + index))
    }

    func moveMenu(_ delta: Int) {
        menuIndex = min(max(0, menuIndex + delta), max(0, menu.count - 1))
        syncMenuWindow()
    }

    func activateMenu() {
        guard menu.indices.contains(menuIndex) else { return }
        let item = menu[menuIndex]
        switch item {
        case "TG ON/OFF": state.tgEnabled.toggle()
        case "DELTA ON/OFF": state.deltaEnabled.toggle()
        case "AUTO TRACK": state.autoTrack.toggle()
        case "MEMORY", "MEMORY ON/OFF": memoryEnabled.toggle()
        case "MARKER TO PEAK": markerToPeak()
        case "MARKER TO MIN SWR": markerToMinimum()
        case "DATA SOURCE": sourceMode = sourceMode == .local ? .usb : .local
        default: break
        }
        refresh()
    }

    func toggleMarker(_ index: Int) {
        guard state.markers.indices.contains(index) else { return }
        selectedMarker = index
        state.markers[index].enabled.toggle()
        refresh()
    }

    func markerToPeak() {
        guard !state.trace.isEmpty else { return }
        let p = state.trace.max(by: { $0.value < $1.value })!
        state.markers[selectedMarker].enabled = true
        state.markers[selectedMarker].frequencyMHz = p.frequencyMHz
        state.markers[selectedMarker].value = p.value
    }

    func markerToMinimum() {
        guard !state.trace.isEmpty else { return }
        let p = state.trace.min(by: { $0.value < $1.value })!
        state.markers[selectedMarker].enabled = true
        state.markers[selectedMarker].frequencyMHz = p.frequencyMHz
        state.markers[selectedMarker].value = p.value
    }

    func deltaText() -> String {
        let enabled = state.markers.filter(\.enabled)
        guard state.deltaEnabled, enabled.count >= 2 else { return state.deltaEnabled ? "DELTA --" : "DELTA OFF" }
        let df = enabled[1].frequencyMHz - enabled[0].frequencyMHz
        let da = enabled[1].value - enabled[0].value
        return String(format: "ΔF %.3f kHz   ΔA %+.2f %@", df * 1000, da, state.mode == .antenna ? "SWR" : "dB")
    }

    private func syncMenuWindow() {
        guard menu.count > 12 else { menuFirst = 0; return }
        if menuIndex < menuFirst { menuFirst = menuIndex }
        if menuIndex >= menuFirst + 12 { menuFirst = menuIndex - 11 }
        menuFirst = min(max(0, menuFirst), menu.count - 12)
    }
}
