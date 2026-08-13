import Foundation

protocol InstrumentDataSource {
    var name: String { get }
    func snapshot(from state: InstrumentSnapshot) -> InstrumentSnapshot
}

struct LocalSimulatorDataSource: InstrumentDataSource {
    let name = "LOCAL SIMULATOR"

    func snapshot(from state: InstrumentSnapshot) -> InstrumentSnapshot {
        var next = state
        let points = 700
        next.trace = (0..<points).map { index in
            let f = state.startMHz + state.spanMHz * Double(index) / Double(points - 1)
            let baseline = -87.0 + 2.0 * sin(f * 7.1)
            let p1 = gaussian(f, center: 145.425, width: 0.020, peak: -19.2, floor: baseline)
            let p2 = gaussian(f, center: 146.195, width: 0.028, peak: -39.0, floor: baseline)
            let value: Double
            switch state.mode {
            case .duplex:
                let n1 = notch(f, center: 145.425, width: 0.026, depth: 74, baseline: -8)
                let n2 = notch(f, center: 146.195, width: 0.030, depth: 67, baseline: -9)
                value = min(n1, n2)
            case .loss:
                value = -2.3 - 0.8 * sin((f - state.centerMHz) * 3.0)
            case .antenna:
                let dip = 1.05 + 2.2 * pow((f - 145.425) / max(0.08, state.spanMHz / 6), 2)
                value = min(10.0, dip)
            default:
                value = max(p1, p2)
            }
            return TracePoint(frequencyMHz: f, value: value)
        }
        next.markers = next.markers.map { marker in
            guard marker.enabled else { return marker }
            var m = marker
            m.value = interpolate(trace: next.trace, at: marker.frequencyMHz)
            return m
        }
        return next
    }

    private func gaussian(_ x: Double, center: Double, width: Double, peak: Double, floor: Double) -> Double {
        let shape = exp(-0.5 * pow((x - center) / width, 2))
        return floor + (peak - floor) * shape
    }

    private func notch(_ x: Double, center: Double, width: Double, depth: Double, baseline: Double) -> Double {
        baseline - depth * exp(-0.5 * pow((x - center) / width, 2))
    }

    private func interpolate(trace: [TracePoint], at frequency: Double) -> Double {
        guard let p = trace.min(by: { abs($0.frequencyMHz - frequency) < abs($1.frequencyMHz - frequency) }) else { return 0 }
        return p.value
    }
}

/// Placeholder for the future wired accessory transport.
/// No Wi-Fi or Bluetooth code is present in the iPhone simulator.
struct USBInstrumentDataSource: InstrumentDataSource {
    let name = "USB"
    func snapshot(from state: InstrumentSnapshot) -> InstrumentSnapshot { state }
}
