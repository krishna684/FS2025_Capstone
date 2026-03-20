import SwiftUI

struct StatCardView: View {
    let icon: String
    let label: String
    let value: String
    var subtitle: String? = nil
    let color: Color
    let colors: AppColors

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            RoundedRectangle(cornerRadius: 10)
                .fill(color.opacity(0.15))
                .frame(width: 40, height: 40)
                .overlay(Image(systemName: icon).foregroundColor(color))

            Text(value).font(.title2.bold()).foregroundColor(colors.text)
            Text(label).font(.caption).foregroundColor(colors.textSecondary)

            if let sub = subtitle {
                Text(sub).font(.caption2.bold()).foregroundColor(color)
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(colors.card)
        .cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(colors.border))
    }
}

struct SeverityBadge: View {
    let severity: String
    let colors: AppColors

    var color: Color { severityColor(severity, colors: colors) }

    var body: some View {
        Text(severity)
            .font(.caption2.bold())
            .foregroundColor(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 3)
            .background(color.opacity(0.15))
            .cornerRadius(10)
    }
}
