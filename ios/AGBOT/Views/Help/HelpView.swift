import SwiftUI

struct HelpView: View {
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager

    var c: AppColors { themeManager.colors }

    let faqs: [(String, String)] = [
        ("How do I scan a plant?", "Go to the Scan tab, take a photo or select from your gallery, then tap Analyze. Our AI will identify any pests or diseases."),
        ("What plants are supported?", "AGBOT supports a wide range of crops including tomatoes, corn, rice, wheat, cotton, potatoes, soybeans, coffee, tea, and sugarcane."),
        ("How accurate is the AI?", "Our AI model achieves over 90% accuracy on common pests and diseases. Accuracy improves with clear, well-lit photos."),
        ("Can I use it offline?", "Currently, AGBOT requires an internet connection to analyze images. We're working on offline support for future updates."),
        ("How do I describe symptoms?", "Use the Describe tab to type your observations. Include details like leaf color changes, spots, wilting patterns, and affected plant parts."),
        ("Is my data private?", "Yes, your scan data is stored securely and only accessible to you. We do not share your data with third parties.")
    ]

    let quickSteps: [(String, String, String)] = [
        ("1", "camera.fill", "Take a clear photo of the affected plant"),
        ("2", "wand.and.stars", "Let AI analyze the image"),
        ("3", "list.clipboard.fill", "Review diagnosis and treatments"),
        ("4", "checkmark.shield.fill", "Apply recommended solutions")
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Quick Start
                VStack(alignment: .leading, spacing: 12) {
                    Text(translations.t("help.quickStart")).font(.title3.bold()).foregroundColor(c.text)
                    ForEach(quickSteps, id: \.0) { step in
                        HStack(spacing: 12) {
                            Circle().fill(c.primary).frame(width: 36, height: 36)
                                .overlay(Text(step.0).font(.subheadline.bold()).foregroundColor(.white))
                            Image(systemName: step.1).foregroundColor(c.primary).frame(width: 24)
                            Text(step.2).font(.subheadline).foregroundColor(c.text)
                        }
                    }
                }
                .padding(16).background(c.card).cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))

                // FAQ
                VStack(alignment: .leading, spacing: 12) {
                    Text(translations.t("help.faq")).font(.title3.bold()).foregroundColor(c.text)
                    ForEach(faqs, id: \.0) { faq in
                        FAQItem(question: faq.0, answer: faq.1, colors: c)
                    }
                }
                .padding(16).background(c.card).cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))

                // Pro Tips
                VStack(alignment: .leading, spacing: 12) {
                    Text(translations.t("help.tips")).font(.title3.bold()).foregroundColor(c.text)
                    tipRow("sun.max.fill", "Take photos in good lighting for best results", c.warning)
                    tipRow("camera.macro", "Get close to the affected area", c.primary)
                    tipRow("arrow.triangle.2.circlepath", "Scan regularly to track plant health over time", c.success)
                    tipRow("doc.text", "Use Describe mode when photos aren't possible", c.info)
                }
                .padding(16).background(c.card).cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
            }
            .padding(16)
        }
        .background(c.background.ignoresSafeArea())
    }

    func tipRow(_ icon: String, _ text: String, _ color: Color) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon).foregroundColor(color).frame(width: 24)
            Text(text).font(.subheadline).foregroundColor(c.textSecondary)
        }
    }
}

struct FAQItem: View {
    let question: String
    let answer: String
    let colors: AppColors
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button { withAnimation { isExpanded.toggle() } } label: {
                HStack {
                    Text(question).font(.subheadline.bold()).foregroundColor(colors.text).multilineTextAlignment(.leading)
                    Spacer()
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down").foregroundColor(colors.textSecondary)
                }
            }
            if isExpanded {
                Text(answer).font(.caption).foregroundColor(colors.textSecondary).padding(.top, 8)
            }
        }
        .padding(12)
        .background(colors.background)
        .cornerRadius(10)
    }
}
