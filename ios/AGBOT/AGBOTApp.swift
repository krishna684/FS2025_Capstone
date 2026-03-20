import SwiftUI

@main
struct AGBOTApp: App {
    @StateObject private var auth = AuthManager()
    @StateObject private var themeManager = ThemeManager()
    @StateObject private var translations = TranslationManager()

    var body: some Scene {
        WindowGroup {
            Group {
                if auth.isLoading {
                    splashScreen
                } else if auth.isLoggedIn {
                    MainTabView()
                } else {
                    LoginView()
                }
            }
            .environmentObject(auth)
            .environmentObject(themeManager)
            .environmentObject(translations)
        }
    }

    var splashScreen: some View {
        ZStack {
            themeManager.colors.background.ignoresSafeArea()
            VStack(spacing: 16) {
                Circle()
                    .fill(themeManager.colors.primary.opacity(0.15))
                    .frame(width: 100, height: 100)
                    .overlay(Image(systemName: "leaf.fill").font(.system(size: 44)).foregroundColor(themeManager.colors.primary))
                Text("AGBOT").font(.system(size: 36, weight: .heavy)).foregroundColor(themeManager.colors.primary)
                ProgressView().tint(themeManager.colors.primary)
            }
        }
    }
}

struct MainTabView: View {
    @EnvironmentObject var auth: AuthManager
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager

    var c: AppColors { themeManager.colors }

    var body: some View {
        NavigationStack {
            TabView {
                DashboardView()
                    .tabItem { Label(translations.t("nav.dashboard"), systemImage: "house.fill") }

                ScanView()
                    .tabItem { Label(translations.t("nav.scan"), systemImage: "camera.fill") }

                DescribeView()
                    .tabItem { Label(translations.t("nav.describe"), systemImage: "text.bubble.fill") }

                HistoryView()
                    .tabItem { Label(translations.t("nav.history"), systemImage: "clock.fill") }

                SettingsView()
                    .tabItem { Label(translations.t("nav.settings"), systemImage: "gearshape.fill") }
            }
            .tint(c.primary)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        NavigationLink { HelpView() } label: {
                            Label(translations.t("nav.help"), systemImage: "questionmark.circle")
                        }
                        NavigationLink { AboutView() } label: {
                            Label(translations.t("nav.about"), systemImage: "info.circle")
                        }
                        Button(role: .destructive) { auth.logout() } label: {
                            Label(translations.t("nav.logout"), systemImage: "rectangle.portrait.and.arrow.right")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle").foregroundColor(c.primary)
                    }
                }
            }
        }
    }
}
