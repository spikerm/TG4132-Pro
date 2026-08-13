import SwiftUI

struct InstrumentScreen: View {
    @EnvironmentObject private var model: InstrumentViewModel

    var body: some View {
        GeometryReader { geo in
            HStack(spacing: 0) {
                VStack(spacing: 6) {
                    header
                    measurementBar
                    CRTGraphView()
                        .environmentObject(model)
                    frequencyBar
                    markerBank
                    statusBars
                    softKeys
                }
                .padding(10)

                if model.menuVisible {
                    Divider().overlay(Color.green.opacity(0.65))
                    menuPanel
                        .frame(width: min(290, geo.size.width * 0.27))
                        .padding(.horizontal, 8)
                }
            }
            .background(Color(red: 0.005, green: 0.035, blue: 0.018))
            .foregroundStyle(.green)
            .font(.system(size: 12, weight: .medium, design: .monospaced))
        }
        .ignoresSafeArea(.container, edges: .all)
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 2) {
                Text("TR4132N / TR1604-PRO     \(model.state.mode.rawValue)")
                    .font(.system(size: 16, weight: .bold, design: .monospaced))
                Text(String(format: "CENTER %.6f MHz", model.state.centerMHz))
                Text(String(format: "SPAN   %.6f MHz", model.state.spanMHz))
            }
            Spacer()
            VStack(alignment: .leading, spacing: 2) {
                Text(String(format: "RBW %.0f kHz", model.state.rbwKHz))
                Text(String(format: "VBW %.0f kHz", model.state.vbwKHz))
                if model.state.mode == .antenna {
                    Text("SWR SCALE")
                } else {
                    Text(String(format: "REF %.1f dBm", model.state.refLevelDBm))
                }
            }
            Spacer()
            Text(model.state.tgEnabled ? String(format: "TG ON   %.1f dBm", model.state.tgLevelDBm) : "TG OFF")
                .font(.system(size: 15, weight: .bold, design: .monospaced))
        }
    }

    private var measurementBar: some View {
        HStack {
            let marker = model.state.markers[model.selectedMarker]
            if marker.enabled {
                Text(String(format: "> M%d   %.6f MHz   %.2f %@", marker.id, marker.frequencyMHz, marker.value, model.state.mode == .antenna ? "SWR" : "dB"))
                    .foregroundStyle(.yellow)
            } else {
                Text("> M\(marker.id) OFF").foregroundStyle(.secondary)
            }
            Spacer()
            Text(model.deltaText()).foregroundStyle(model.state.deltaEnabled ? .yellow : .secondary)
        }
        .padding(.vertical, 2)
    }

    private var frequencyBar: some View {
        HStack {
            Text(String(format: "START %.6f MHz", model.state.startMHz))
            Spacer()
            Text(String(format: "CENTER %.6f MHz", model.state.centerMHz))
            Spacer()
            Text(String(format: "STOP %.6f MHz", model.state.stopMHz))
        }
    }

    private var markerBank: some View {
        HStack(spacing: 4) {
            ForEach(Array(model.state.markers.enumerated()), id: \.element.id) { index, marker in
                Button {
                    model.toggleMarker(index)
                } label: {
                    VStack(spacing: 2) {
                        Text("M\(marker.id) \(marker.enabled ? "ON" : "OFF")")
                        Text(String(format: "%.6f MHz", marker.frequencyMHz))
                        Text(marker.enabled ? String(format: "%.2f %@", marker.value, model.state.mode == .antenna ? "SWR" : "dB") : "OFF")
                    }
                    .frame(maxWidth: .infinity, minHeight: 55)
                    .overlay(RoundedRectangle(cornerRadius: 2).stroke(index == model.selectedMarker ? Color.white : Color.green.opacity(0.35), lineWidth: index == model.selectedMarker ? 1.5 : 1))
                }
                .buttonStyle(.plain)
                .foregroundStyle(marker.enabled ? (index == 0 ? Color.yellow : index == 1 ? Color.cyan : Color.green) : Color.secondary)
            }
        }
    }

    private var statusBars: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("TRACE A LIVE   MEM B \(model.memoryEnabled ? "ON" : "OFF")   \(model.deltaText())   AUTO \(model.state.autoTrack ? "ON" : "OFF")   \(model.state.tgEnabled ? String(format: "TG %.1f dBm", model.state.tgLevelDBm) : "TG OFF")")
            Text("READY   DATA \(model.sourceMode.rawValue)   \(model.firmware)   \(model.core)")
                .foregroundStyle(.cyan)
        }
    }

    private var softKeys: some View {
        HStack(spacing: 5) {
            modeButton("F1", .spectrum)
            modeButton("F2", .duplex)
            modeButton("F3", .memory)
            modeButton("F4", .antenna)
            Button("F5 MARKER") { model.selectedMarker = (model.selectedMarker + 1) % 4 }
            Button("F6 PEAK") { model.markerToPeak(); model.refresh() }
            modeButton("F7", .loss)
            Button("F8 SETUP") { model.setMode(.setup) }
            Button(model.menuVisible ? "MENU OFF" : "MENU ON") { model.toggleMenu() }
        }
        .buttonStyle(.borderless)
        .font(.system(size: 10, weight: .semibold, design: .monospaced))
    }

    private func modeButton(_ key: String, _ mode: InstrumentMode) -> some View {
        Button("\(key) \(mode.rawValue)") { model.setMode(mode) }
    }

    private var menuPanel: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(model.state.mode.rawValue)
                .font(.system(size: 15, weight: .bold, design: .monospaced))
                .padding(.bottom, 4)

            ForEach(Array(model.visibleMenu.enumerated()), id: \.offset) { row, item in
                let absolute = model.menuFirst + row
                Button {
                    model.selectMenu(relative: row)
                    model.activateMenu()
                } label: {
                    HStack {
                        Text(absolute == model.menuIndex ? "> " : "  ")
                        Text(item)
                        Spacer()
                    }
                    .padding(.vertical, 3)
                    .padding(.horizontal, 4)
                    .overlay(RoundedRectangle(cornerRadius: 2).stroke(absolute == model.menuIndex ? Color.green : Color.clear))
                    .foregroundStyle(absolute == model.menuIndex ? .yellow : .green)
                }
                .buttonStyle(.plain)
            }

            Spacer(minLength: 2)
            Text(model.menuPageText)
                .foregroundStyle(.secondary)
                .font(.system(size: 10, design: .monospaced))
            HStack {
                Button("▲") { model.moveMenu(-1) }
                Button("ENTER") { model.activateMenu() }
                Button("▼") { model.moveMenu(1) }
            }
            .buttonStyle(.bordered)
            .controlSize(.small)
        }
        .padding(.vertical, 10)
    }
}

struct CRTGraphView: View {
    @EnvironmentObject private var model: InstrumentViewModel

    var body: some View {
        Canvas { context, size in
            let left: CGFloat = 42
            let right: CGFloat = size.width - 6
            let top: CGFloat = 5
            let bottom: CGFloat = size.height - 5
            let plot = CGRect(x: left, y: top, width: right - left, height: bottom - top)

            var grid = Path()
            for i in 0...10 {
                let x = plot.minX + plot.width * CGFloat(i) / 10
                let y = plot.minY + plot.height * CGFloat(i) / 10
                grid.move(to: CGPoint(x: x, y: plot.minY)); grid.addLine(to: CGPoint(x: x, y: plot.maxY))
                grid.move(to: CGPoint(x: plot.minX, y: y)); grid.addLine(to: CGPoint(x: plot.maxX, y: y))

                let label: String
                if model.state.mode == .antenna {
                    label = String(format: "%.1f", 5.0 - 4.0 * Double(i) / 10.0)
                } else {
                    label = String(format: "%.0f", model.state.refLevelDBm - 10.0 * Double(i))
                }
                context.draw(Text(label).font(.system(size: 9, design: .monospaced)).foregroundColor(.green), at: CGPoint(x: left - 18, y: y), anchor: .center)
            }
            context.stroke(grid, with: .color(.green.opacity(0.22)), lineWidth: 0.7)

            guard model.state.trace.count > 1 else { return }
            var trace = Path()
            for (index, p) in model.state.trace.enumerated() {
                let x = plot.minX + plot.width * CGFloat((p.frequencyMHz - model.state.startMHz) / max(0.000001, model.state.spanMHz))
                let norm: Double
                if model.state.mode == .antenna {
                    norm = 1.0 - (min(5.0, max(1.0, p.value)) - 1.0) / 4.0
                } else {
                    norm = (model.state.refLevelDBm - min(model.state.refLevelDBm, max(model.state.refLevelDBm - 100.0, p.value))) / 100.0
                }
                let y = plot.minY + plot.height * CGFloat(norm)
                if index == 0 { trace.move(to: CGPoint(x: x, y: y)) } else { trace.addLine(to: CGPoint(x: x, y: y)) }
            }
            context.stroke(trace, with: .color(.green), lineWidth: 1.2)

            let colors: [Color] = [.yellow, .cyan, .green, .white]
            for (index, marker) in model.state.markers.enumerated() where marker.enabled {
                guard marker.frequencyMHz >= model.state.startMHz, marker.frequencyMHz <= model.state.stopMHz else { continue }
                let x = plot.minX + plot.width * CGFloat((marker.frequencyMHz - model.state.startMHz) / model.state.spanMHz)
                var markerPath = Path()
                markerPath.move(to: CGPoint(x: x, y: plot.minY))
                markerPath.addLine(to: CGPoint(x: x, y: plot.maxY))
                context.stroke(markerPath, with: .color(colors[index].opacity(0.8)), style: StrokeStyle(lineWidth: 0.8, dash: [4, 4]))
                context.draw(Text("M\(marker.id)").font(.system(size: 10, weight: .bold, design: .monospaced)).foregroundColor(colors[index]), at: CGPoint(x: x + 2, y: plot.minY + 12), anchor: .leading)
            }
        }
        .frame(minHeight: 190)
        .overlay(Rectangle().stroke(Color.green.opacity(0.75), lineWidth: 1))
    }
}
