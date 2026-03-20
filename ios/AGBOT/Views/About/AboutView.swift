import SwiftUI

struct AboutView: View {
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager

    var c: AppColors { themeManager.colors }

    let teamMembers: [(String, String, String)] = [
        ("Dr. Sarah Chen", "Lead AI Researcher", "brain.head.profile"),
        ("James Ochieng", "Agricultural Expert", "leaf.fill"),
        ("Priya Sharma", "Mobile Developer", "iphone"),
        ("Carlos Rivera", "Backend Engineer", "server.rack")
    ]

    let impactStats: [(String, String, String)] = [
        ("50K+", "Scans Performed", "doc.text.magnifyingglass"),
        ("120+", "Countries Served", "globe"),
        ("95%", "User Satisfaction", "hand.thumbsup.fill"),
        ("30+", "Pest Species", "ant.fill")
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Hero
                VStack(spacing: 12) {
                    Circle().fill(c.primary.opacity(0.15)).frame(width: 80, height: 80)
                        .overlay(Image(systemName: "leaf.fill").font(.system(size: 36)).foregroundColor(c.primary))
                    Text("AGBOT").font(.system(size: 28, weight: .heavy)).foregroundColor(c.primary)
                    Text("From Data to Harvest").font(.subheadline).foregroundColor(c.textSecondary)
                    Text("v1.0.0").font(.caption2).foregroundColor(c.textSecondary)
                }
                .padding(24).frame(maxWidth: .infinity)
                .background(c.card).cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))

                // Mission
                VStack(alignment: .leading, spacing: 8) {
                    Text(translations.t("about.mission")).font(.title3.bold()).foregroundColor(c.text)
                    Text("AGBOT empowers farmers worldwide with AI-powered pest and disease detection. Our mission is to reduce crop losses, increase food security, and make precision agriculture accessible to everyone — from smallholder farms to large-scale operations.")
                        .font(.subheadline).foregroundColor(c.textSecondary).lineSpacing(4)
                }
                .padding(16).background(c.card).cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))

                // Impact
                VStack(alignment: .leading, spacing: 12) {
                    Text(translations.t("about.impact")).font(.title3.bold()).foregroundColor(c.text)
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        ForEach(impactStats, id: \.0) { stat in
                            VStack(spacing: 6) {
                                Image(systemName: stat.2).font(.title3).foregroundColor(c.primary)
                                Text(stat.0).font(.title3.bold()).foregroundColor(c.text)
                                Text(stat.1).font(.caption).foregroundColor(c.textSecondary)
                            }
                            .padding(12).frame(maxWidth: .infinity)
                            .background(c.background).cornerRadius(10)
                        }
                    }
                }
                .padding(16).background(c.card).cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))

                // Team
                VStack(alignment: .leading, spacing: 12) {
                    Text(translations.t("about.team")).font(.title3.bold()).foregroundColor(c.text)
                    ForEach(teamMembers, id: \.0) { member in
                        HStack(spacing: 12) {
                            Circle().fill(c.primary.opacity(0.15)).frame(width: 44, height: 44)
                                .overlay(Image(systemName: member.2).foregroundColor(c.primary))
                            VStack(alignment: .leading, spacing: 2) {
                                Text(member.0).font(.subheadline.bold()).foregroundColor(c.text)
                                Text(member.1).font(.caption).foregroundColor(c.textSecondary)
                            }
                            Spacer()
                        }
                        .padding(10).background(c.background).cornerRadius(10)
                    }
                }
                .padding(16).background(c.card).cornerRadius(14)
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(c.border))
            }
            .padding(16)
        }
        .background(c.background.ignoresSafeArea())
    }
}
