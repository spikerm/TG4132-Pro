import Foundation

enum InstrumentMode: String, CaseIterable, Identifiable {
    case spectrum = "SPECTRUM"
    case duplex = "DUPLEX"
    case memory = "MEMORY"
    case antenna = "ANTENNA"
    case loss = "LOSS"
    case setup = "SETUP"
    var id: String { rawValue }
}

enum DataSourceMode: String, CaseIterable, Identifiable {
    case local = "LOCAL SIMULATOR"
    case usb = "USB"
    var id: String { rawValue }
}

struct TracePoint: Identifiable {
    let id = UUID()
    let frequencyMHz: Double
    let value: Double
}

struct Marker: Identifiable {
    let id: Int
    var enabled: Bool
    var frequencyMHz: Double
    var value: Double
}

struct InstrumentSnapshot {
    var centerMHz: Double = 145.500
    var spanMHz: Double = 2.000
    var rbwKHz: Double = 30
    var vbwKHz: Double = 30
    var refLevelDBm: Double = 0
    var tgEnabled: Bool = true
    var tgLevelDBm: Double = -10
    var deltaEnabled: Bool = true
    var autoTrack: Bool = false
    var mode: InstrumentMode = .spectrum
    var trace: [TracePoint] = []
    var memoryTrace: [TracePoint] = []
    var markers: [Marker] = [
        .init(id: 1, enabled: true,  frequencyMHz: 145.425000, value: -19.4),
        .init(id: 2, enabled: true,  frequencyMHz: 146.195000, value: -39.2),
        .init(id: 3, enabled: false, frequencyMHz: 145.500000, value: -100),
        .init(id: 4, enabled: false, frequencyMHz: 145.500000, value: -100)
    ]

    var startMHz: Double { centerMHz - spanMHz / 2 }
    var stopMHz: Double { centerMHz + spanMHz / 2 }
}
