import SwiftUI

struct ResultsView: View {
    let result: ScanResult
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager

    var c: AppColors { themeManager.colors }

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Status Header
                VStack(spacing: 8) {
                    Image(systemName: result.isHealthy ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                        .font(.system(size: 48))
                        .foregroundColor(result.isHealthy ? c.success : c.danger)
                    Text(result.isHealthy ? "Plant is Healthy!" : translations.t("results.detected"))
                        .font(.title3.bold())
                        .foregroundColor(result.isHealthy ? c.success : c.danger)
                    if !result.isHealthy {
                        Text(result.displayName).font(.title2.bold()).foregroundColor(c.text)
                        if !result.displayScientific.isEmpty {
                            Text("(\(result.displayScientific))").font(.caption).italic().foregroundColor(c.textSecondary)
                        }
                    }
                    if let msg = result.message, result.isHealthy {
                        Text(msg).font(.subheadline).foregroundColor(c.textSecondary).multilineTextAlignment(.center)
                    }
                }
                .padding(20).frame(maxWidth: .infinity)
                .background((result.isHealthy ? c.success : c.danger).opacity(0.08))
                .cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke((result.isHealthy ? c.success : c.danger).opacity(0.3)))

                // Confidence bar
                if let conf = result.confidence, conf > 0 {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(translations.t("results.confidence")).font(.subheadline.bold()).foregroundColor(c.text)
                            Spacer()
                            Text(String(format: "%.1f%%", conf)).font(.subheadline.bold()).foregroundColor(c.primary)
                        }
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 6).fill(c.border).frame(height: 10)
                                RoundedRectangle(cornerRadius: 6).fill(conf > 80 ? c.success : c.warning)
                                    .frame(width: geo.size.width * CGFloat(conf) / 100, height: 10)
                            }
                        }.frame(height: 10)
                    }
                    .padding(16).background(c.card).cornerRadius(14)
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
                }

                // Severity
                if let sev = result.severity, !result.isHealthy {
                    HStack {
                        Text(translations.t("results.severity")).font(.subheadline).foregroundColor(c.textSecondary)
                        Spacer()
                        SeverityBadge(severity: sev, colors: c)
                    }
                    .padding(16).background(c.card).cornerRadius(14)
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
                }

                // Damage Pattern / Description
                if let desc = result.damagePattern ?? result.description, !desc.isEmpty {
                    infoCard("Description", desc, "doc.text.fill")
                }

                // Symptoms
                if let symptoms = result.symptoms, !symptoms.isEmpty {
                    treatmentSection("Symptoms", symptoms, c.warning, "eye.fill")
                }

                // Causes
                if let causes = result.causes, !causes.isEmpty {
                    treatmentSection("Causes", causes, c.info, "info.circle.fill")
                }

                // Treatments
                if let tx = result.treatments {
                    if let items = tx.immediate, !items.isEmpty {
                        treatmentSection(translations.t("results.immediate"), items, c.danger, "bolt.fill")
                    }
                    if let items = tx.ipm, !items.isEmpty {
                        treatmentSection("IPM Treatments", items, c.primary, "leaf.fill")
                    }
                    if let items = tx.prevention, !items.isEmpty {
                        treatmentSection(translations.t("results.preventive"), items, c.info, "shield.fill")
                    }
                }

                // Chemical treatments
                if let chem = result.chemicalTreatments, !chem.isEmpty {
                    treatmentSection("Chemical Treatments", chem, c.warning, "flask.fill")
                }

                // Organic treatments
                if let org = result.organicTreatments, !org.isEmpty {
                    treatmentSection("Organic Treatments", org, c.success, "leaf.fill")
                }

                // Prevention
                if let prev = result.prevention, !prev.isEmpty {
                    treatmentSection(translations.t("results.preventive"), prev, Color.purple, "shield.checkered")
                }

                // Affected Plants
                if let plants = result.affectedPlants, !plants.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "leaf.fill").foregroundColor(c.primary)
                            Text("Affected Plants").font(.subheadline.bold()).foregroundColor(c.text)
                        }
                        FlowLayout(items: plants) { plant in
                            Text(plant).font(.caption).padding(.horizontal, 10).padding(.vertical, 4)
                                .background(c.primary.opacity(0.1)).foregroundColor(c.primary)
                                .cornerRadius(12)
                        }
                    }
                    .padding(16).background(c.card).cornerRadius(14)
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
                }

                // Alternative Predictions
                if let preds = result.allPredictions, preds.count > 1 {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Other Possibilities").font(.subheadline.bold()).foregroundColor(c.text)
                        ForEach(preds.dropFirst().prefix(2), id: \.pest) { pred in
                            HStack {
                                Text(pred.pest).font(.caption).foregroundColor(c.textSecondary)
                                Spacer()
                                Text(String(format: "%.1f%%", pred.confidence)).font(.caption.bold()).foregroundColor(c.textSecondary)
                            }
                        }
                    }
                    .padding(16).background(c.card).cornerRadius(14)
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
                }
            }
            .padding(16)
        }
        .background(c.background.ignoresSafeArea())
        .navigationTitle(translations.t("results.title"))
        .navigationBarTitleDisplayMode(.inline)
    }

    func infoCard(_ label: String, _ value: String, _ icon: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: icon).foregroundColor(c.primary)
                Text(label).font(.subheadline.bold()).foregroundColor(c.text)
            }
            Text(value).font(.caption).foregroundColor(c.textSecondary).lineSpacing(3)
        }
        .padding(16).background(c.card).cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
    }

    func treatmentSection(_ title: String, _ items: [String], _ color: Color, _ icon: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon).foregroundColor(color)
                Text(title).font(.subheadline.bold()).foregroundColor(c.text)
            }
            ForEach(items, id: \.self) { item in
                HStack(alignment: .top, spacing: 8) {
                    Circle().fill(color).frame(width: 6, height: 6).padding(.top, 6)
                    Text(item).font(.caption).foregroundColor(c.textSecondary)
                }
            }
        }
        .padding(16).background(c.card).cornerRadius(14)
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
    }
}

// Simple flow layout for tag chips
struct FlowLayout<Item: Hashable, Content: View>: View {
    let items: [Item]
    let content: (Item) -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            ForEach(0..<((items.count + 2) / 3), id: \.self) { row in
                HStack(spacing: 6) {
                    ForEach(0..<3, id: \.self) { col in
                        let idx = row * 3 + col
                        if idx < items.count {
                            content(items[idx])
                        }
                    }
                }
            }
        }
    }
}
