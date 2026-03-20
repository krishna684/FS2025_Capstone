import SwiftUI
import Charts

struct DashboardView: View {
    @EnvironmentObject var auth: AuthManager
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager
    @State private var dashboard: DashboardResponse?
    @State private var isLoading = true

    var c: AppColors { themeManager.colors }

    var body: some View {
        ScrollView {
            if isLoading {
                ProgressView().padding(.top, 100)
            } else if let d = dashboard {
                VStack(spacing: 16) {
                    header(d)
                    statsGrid(d.userData)
                    if #available(iOS 16.0, *) { pestTrendChart(d.pestTrends) }
                    healthPie(d.healthDistribution)
                    weatherCard(d.weather)
                    recentDetections(d.recentDetections)
                }
                .padding(16)
            } else {
                Text("Failed to load dashboard").foregroundColor(c.textSecondary).padding(.top, 100)
            }
        }
        .background(c.background.ignoresSafeArea())
        .refreshable { await loadDashboard() }
        .task { await loadDashboard() }
    }

    func header(_ d: DashboardResponse) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(translations.t("dashboard.welcome")).font(.title2.bold()).foregroundColor(c.text)
                Text(d.currentDate).font(.caption).foregroundColor(c.textSecondary)
            }
            Spacer()
            Circle()
                .fill(c.primary.opacity(0.15))
                .frame(width: 44, height: 44)
                .overlay(Image(systemName: "leaf.fill").foregroundColor(c.primary))
        }
    }

    func statsGrid(_ stats: UserStats) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
            StatCardView(icon: "doc.text.magnifyingglass", label: translations.t("dashboard.totalScans"), value: "\(stats.totalScans)", color: c.primary, colors: c)
            StatCardView(icon: "heart.fill", label: translations.t("dashboard.healthRate"), value: "\(stats.healthyPercentage)%", color: c.success, colors: c)
            StatCardView(icon: "ant.fill", label: translations.t("dashboard.pestsFound"), value: "\(stats.pestsDetected)", color: c.warning, colors: c)
            StatCardView(icon: "cpu", label: translations.t("dashboard.aiAccuracy"), value: "\(stats.aiAccuracy)%", color: c.info, colors: c)
        }
    }

    @available(iOS 16.0, *)
    func pestTrendChart(_ trends: PestTrends) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(translations.t("dashboard.pestTrends")).font(.headline).foregroundColor(c.text)
            Chart {
                ForEach(Array(zip(trends.months, trends.values)), id: \.0) { month, value in
                    LineMark(x: .value("Month", month), y: .value("Count", value))
                        .foregroundStyle(c.primary)
                    AreaMark(x: .value("Month", month), y: .value("Count", value))
                        .foregroundStyle(c.primary.opacity(0.1))
                }
            }
            .frame(height: 200)
            .chartYAxis { AxisMarks(position: .leading) }
        }
        .padding(16)
        .background(c.card)
        .cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
    }

    func healthPie(_ dist: HealthDistribution) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(translations.t("dashboard.healthDist")).font(.headline).foregroundColor(c.text)
            HStack(spacing: 12) {
                healthRow("Healthy", dist.healthy, c.success)
                healthRow("Pest", dist.pestDamage, c.warning)
                healthRow("Disease", dist.disease, c.info)
                healthRow("Critical", dist.critical, c.danger)
            }
        }
        .padding(16)
        .background(c.card)
        .cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
    }

    func healthRow(_ label: String, _ value: Int, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Circle().fill(color).frame(width: 12, height: 12)
            Text("\(value)%").font(.caption.bold()).foregroundColor(c.text)
            Text(label).font(.caption2).foregroundColor(c.textSecondary)
        }.frame(maxWidth: .infinity)
    }

    func weatherCard(_ w: Weather) -> some View {
        HStack {
            Image(systemName: w.condition.lowercased().contains("sun") ? "sun.max.fill" : "cloud.fill")
                .font(.title).foregroundColor(c.warning)
            VStack(alignment: .leading) {
                Text("\(w.temperature)°C").font(.title3.bold()).foregroundColor(c.text)
                Text(w.condition).font(.caption).foregroundColor(c.textSecondary)
            }
            Spacer()
            VStack(alignment: .trailing) {
                Text("Humidity").font(.caption2).foregroundColor(c.textSecondary)
                Text("\(w.humidity)%").font(.subheadline.bold()).foregroundColor(c.info)
            }
        }
        .padding(16)
        .background(c.card)
        .cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
    }

    func recentDetections(_ detections: [Detection]) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(translations.t("dashboard.recentDetections")).font(.headline).foregroundColor(c.text)
            ForEach(detections) { d in
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(d.pest).font(.subheadline.bold()).foregroundColor(c.text)
                        Text("\(d.crop) • \(d.field)").font(.caption).foregroundColor(c.textSecondary)
                    }
                    Spacer()
                    SeverityBadge(severity: d.severity, colors: c)
                }
                .padding(12)
                .background(c.background)
                .cornerRadius(10)
            }
        }
        .padding(16)
        .background(c.card)
        .cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
    }

    func loadDashboard() async {
        isLoading = true
        do { dashboard = try await APIService.shared.getDashboard() }
        catch { print("Dashboard error: \(error)") }
        isLoading = false
    }
}
