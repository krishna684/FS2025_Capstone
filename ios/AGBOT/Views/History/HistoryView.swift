import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager
    @State private var history: [HistoryItem] = []
    @State private var isLoading = true
    @State private var searchText = ""
    @State private var filterSeverity = "All"

    var c: AppColors { themeManager.colors }
    let severities = ["All", "Critical", "High", "Medium", "Low", "Healthy"]

    var filtered: [HistoryItem] {
        history.filter { item in
            let matchSearch = searchText.isEmpty || item.pest.localizedCaseInsensitiveContains(searchText) || item.crop.localizedCaseInsensitiveContains(searchText)
            let matchSeverity = filterSeverity == "All" || item.severity.lowercased() == filterSeverity.lowercased()
            return matchSearch && matchSeverity
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass").foregroundColor(c.textSecondary)
                TextField(translations.t("history.search"), text: $searchText)
            }
            .padding(.horizontal, 14).frame(height: 44)
            .background(c.card).cornerRadius(12)
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
            .padding(.horizontal, 16).padding(.top, 12)

            // Filter chips
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(severities, id: \.self) { sev in
                        Button(sev) { filterSeverity = sev }
                            .font(.caption.bold())
                            .padding(.horizontal, 12).padding(.vertical, 6)
                            .background(filterSeverity == sev ? c.primary : c.card)
                            .foregroundColor(filterSeverity == sev ? .white : c.text)
                            .cornerRadius(16)
                            .overlay(RoundedRectangle(cornerRadius: 16).stroke(filterSeverity == sev ? c.primary : c.border))
                    }
                }.padding(.horizontal, 16).padding(.vertical, 8)
            }

            if isLoading {
                Spacer()
                ProgressView()
                Spacer()
            } else if filtered.isEmpty {
                Spacer()
                VStack(spacing: 8) {
                    Image(systemName: "doc.text.magnifyingglass").font(.system(size: 40)).foregroundColor(c.textSecondary)
                    Text(translations.t("history.empty")).foregroundColor(c.textSecondary)
                }
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: 10) {
                        ForEach(filtered) { item in
                            historyRow(item)
                        }
                    }.padding(16)
                }
                .refreshable { await loadHistory() }
            }
        }
        .background(c.background.ignoresSafeArea())
        .task { await loadHistory() }
    }

    func historyRow(_ item: HistoryItem) -> some View {
        HStack {
            RoundedRectangle(cornerRadius: 8)
                .fill(severityColor(item.severity, colors: c).opacity(0.15))
                .frame(width: 44, height: 44)
                .overlay(Image(systemName: "ant.fill").foregroundColor(severityColor(item.severity, colors: c)))
            VStack(alignment: .leading, spacing: 2) {
                Text(item.pest).font(.subheadline.bold()).foregroundColor(c.text)
                Text("\(item.crop) • \(item.field)").font(.caption).foregroundColor(c.textSecondary)
                Text(item.date).font(.caption2).foregroundColor(c.textSecondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                SeverityBadge(severity: item.severity, colors: c)
                Text("\(item.confidence)%").font(.caption2).foregroundColor(c.textSecondary)
            }
        }
        .padding(12)
        .background(c.card)
        .cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
    }

    func loadHistory() async {
        isLoading = true
        do {
            let response = try await APIService.shared.getHistory()
            history = response.history
        } catch { print("History error: \(error)") }
        isLoading = false
    }
}
