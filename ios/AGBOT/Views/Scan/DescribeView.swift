import SwiftUI

struct DescribeView: View {
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager
    @State private var symptoms = ""
    @State private var selectedPlant = ""
    @State private var isAnalyzing = false
    @State private var scanResult: ScanResult?
    @State private var showResult = false
    @State private var errorMessage: String?

    var c: AppColors { themeManager.colors }

    let plantTypes = ["Tomato", "Corn", "Rice", "Wheat", "Cotton", "Potato", "Soybean", "Coffee", "Tea", "Sugarcane"]

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text(translations.t("describe.title")).font(.title2.bold()).foregroundColor(c.text)
                Text(translations.t("describe.subtitle")).font(.subheadline).foregroundColor(c.textSecondary)

                VStack(alignment: .leading, spacing: 8) {
                    Text(translations.t("describe.plantType")).font(.subheadline.bold()).foregroundColor(c.text)
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(plantTypes, id: \.self) { plant in
                                Button(plant) { selectedPlant = plant }
                                    .font(.subheadline)
                                    .padding(.horizontal, 14).padding(.vertical, 8)
                                    .background(selectedPlant == plant ? c.primary : c.card)
                                    .foregroundColor(selectedPlant == plant ? .white : c.text)
                                    .cornerRadius(20)
                                    .overlay(RoundedRectangle(cornerRadius: 20).stroke(selectedPlant == plant ? c.primary : c.border))
                            }
                        }
                    }
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text(translations.t("describe.symptoms")).font(.subheadline.bold()).foregroundColor(c.text)
                    TextEditor(text: $symptoms)
                        .frame(minHeight: 120)
                        .padding(8)
                        .background(c.card)
                        .cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
                }

                if let error = errorMessage {
                    Text(error).font(.caption).foregroundColor(c.danger)
                }

                Button {
                    Task { await analyzeSymptoms() }
                } label: {
                    if isAnalyzing {
                        HStack { ProgressView().tint(.white); Text("Analyzing...").foregroundColor(.white) }
                    } else {
                        Label(translations.t("describe.analyze"), systemImage: "wand.and.stars")
                    }
                }
                .frame(maxWidth: .infinity).frame(height: 50)
                .background((symptoms.isEmpty || selectedPlant.isEmpty) ? c.textSecondary : c.primary)
                .foregroundColor(.white).cornerRadius(12).fontWeight(.bold)
                .disabled(symptoms.isEmpty || selectedPlant.isEmpty || isAnalyzing)
            }
            .padding(20)
        }
        .background(c.background.ignoresSafeArea())
        .navigationDestination(isPresented: $showResult) {
            if let result = scanResult { ResultsView(result: result) }
        }
    }

    func analyzeSymptoms() async {
        isAnalyzing = true; errorMessage = nil
        do {
            scanResult = try await APIService.shared.analyzeSymptoms(symptoms: symptoms, plantType: selectedPlant)
            showResult = true
        } catch { errorMessage = error.localizedDescription }
        isAnalyzing = false
    }
}
