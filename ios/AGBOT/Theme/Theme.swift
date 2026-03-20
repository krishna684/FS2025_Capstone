import SwiftUI

struct AppColors {
    let primary: Color
    let secondary: Color
    let background: Color
    let card: Color
    let text: Color
    let textSecondary: Color
    let border: Color
    let success: Color
    let warning: Color
    let danger: Color
    let info: Color

    static let light = AppColors(
        primary: Color(hex: "16a34a"), secondary: Color(hex: "ff6b35"),
        background: Color(hex: "f8fafb"), card: .white,
        text: Color(hex: "1f2937"), textSecondary: Color(hex: "6b7280"),
        border: Color(hex: "e5e7eb"), success: Color(hex: "10b981"),
        warning: Color(hex: "fbbf24"), danger: Color(hex: "ef4444"),
        info: Color(hex: "3b82f6")
    )

    static let dark = AppColors(
        primary: Color(hex: "22c55e"), secondary: Color(hex: "ff6b35"),
        background: Color(hex: "0f172a"), card: Color(hex: "1e293b"),
        text: Color(hex: "f1f5f9"), textSecondary: Color(hex: "94a3b8"),
        border: Color(hex: "334155"), success: Color(hex: "10b981"),
        warning: Color(hex: "fbbf24"), danger: Color(hex: "ef4444"),
        info: Color(hex: "3b82f6")
    )
}

@MainActor
class ThemeManager: ObservableObject {
    @AppStorage("isDark") var isDark = false

    var colors: AppColors { isDark ? .dark : .light }

    func toggle() { isDark.toggle() }
}

func severityColor(_ severity: String, colors: AppColors) -> Color {
    switch severity {
    case "Healthy": return colors.success
    case "Mild": return colors.info
    case "Moderate": return colors.warning
    case "High", "Severe": return colors.danger
    default: return colors.textSecondary
    }
}

// MARK: - Color Hex Extension

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 6: (a, r, g, b) = (255, (int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF)
        case 8: (a, r, g, b) = ((int >> 24) & 0xFF, (int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF)
        default: (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(.sRGB, red: Double(r) / 255, green: Double(g) / 255, blue: Double(b) / 255, opacity: Double(a) / 255)
    }
}
