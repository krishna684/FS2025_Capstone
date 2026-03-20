import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var auth: AuthManager
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager
    @State private var selectedTab = 0
    @State private var name = ""
    @State private var email = ""
    @State private var phone = ""
    @State private var location = ""
    @State private var currentPassword = ""
    @State private var newPassword = ""
    @State private var confirmPassword = ""
    @State private var successMessage: String?
    @State private var errorMessage: String?
    @State private var isLoading = false

    var c: AppColors { themeManager.colors }

    var body: some View {
        VStack(spacing: 0) {
            // Tab selector
            HStack(spacing: 0) {
                tabButton(translations.t("settings.profile"), 0)
                tabButton(translations.t("settings.preferences"), 1)
                tabButton(translations.t("settings.security"), 2)
            }
            .background(c.card)

            ScrollView {
                VStack(spacing: 16) {
                    switch selectedTab {
                    case 0: profileTab
                    case 1: preferencesTab
                    case 2: securityTab
                    default: EmptyView()
                    }

                    if let msg = successMessage {
                        Text(msg).font(.caption).foregroundColor(c.success)
                    }
                    if let err = errorMessage {
                        Text(err).font(.caption).foregroundColor(c.danger)
                    }
                }.padding(16)
            }
        }
        .background(c.background.ignoresSafeArea())
        .onAppear { loadProfile() }
    }

    func tabButton(_ title: String, _ index: Int) -> some View {
        Button { selectedTab = index; successMessage = nil; errorMessage = nil } label: {
            Text(title).font(.subheadline.bold())
                .foregroundColor(selectedTab == index ? c.primary : c.textSecondary)
                .frame(maxWidth: .infinity).padding(.vertical, 12)
                .overlay(alignment: .bottom) {
                    if selectedTab == index {
                        Rectangle().fill(c.primary).frame(height: 2)
                    }
                }
        }
    }

    var profileTab: some View {
        VStack(spacing: 12) {
            settingsField("person", translations.t("settings.name"), $name)
            settingsField("envelope", translations.t("settings.email"), $email, keyboard: .emailAddress)
            settingsField("phone", translations.t("settings.phone"), $phone, keyboard: .phonePad)
            settingsField("location", translations.t("settings.location"), $location)
            saveButton { await saveProfile() }
        }
    }

    var preferencesTab: some View {
        VStack(spacing: 16) {
            // Theme toggle
            HStack {
                Image(systemName: themeManager.isDark ? "moon.fill" : "sun.max.fill").foregroundColor(c.primary)
                Text(translations.t("settings.darkMode")).foregroundColor(c.text)
                Spacer()
                Toggle("", isOn: $themeManager.isDark).labelsHidden()
            }
            .padding(16).background(c.card).cornerRadius(12)
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))

            // Language picker
            VStack(alignment: .leading, spacing: 8) {
                Text(translations.t("settings.language")).font(.subheadline.bold()).foregroundColor(c.text)
                ForEach(["en", "es", "hi", "sw"], id: \.self) { lang in
                    Button {
                        translations.currentLanguage = lang
                    } label: {
                        HStack {
                            Text(langName(lang)).foregroundColor(c.text)
                            Spacer()
                            if translations.currentLanguage == lang {
                                Image(systemName: "checkmark").foregroundColor(c.primary)
                            }
                        }
                        .padding(12)
                        .background(translations.currentLanguage == lang ? c.primary.opacity(0.1) : c.card)
                        .cornerRadius(10)
                    }
                }
            }
            .padding(16).background(c.card).cornerRadius(12)
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
        }
    }

    var securityTab: some View {
        VStack(spacing: 12) {
            secureSettingsField("lock", translations.t("settings.currentPassword"), $currentPassword)
            secureSettingsField("lock", translations.t("settings.newPassword"), $newPassword)
            secureSettingsField("lock", translations.t("settings.confirmPassword"), $confirmPassword)
            saveButton { await changePassword() }
        }
    }

    func settingsField(_ icon: String, _ placeholder: String, _ text: Binding<String>, keyboard: UIKeyboardType = .default) -> some View {
        HStack {
            Image(systemName: icon).foregroundColor(c.textSecondary)
            TextField(placeholder, text: text).keyboardType(keyboard)
        }
        .padding(.horizontal, 14).frame(height: 48)
        .background(c.card).cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
    }

    func secureSettingsField(_ icon: String, _ placeholder: String, _ text: Binding<String>) -> some View {
        HStack {
            Image(systemName: icon).foregroundColor(c.textSecondary)
            SecureField(placeholder, text: text)
        }
        .padding(.horizontal, 14).frame(height: 48)
        .background(c.card).cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
    }

    func saveButton(_ action: @escaping () async -> Void) -> some View {
        Button { Task { await action() } } label: {
            if isLoading { ProgressView().tint(.white) }
            else { Text(translations.t("settings.save")).fontWeight(.bold) }
        }
        .frame(maxWidth: .infinity).frame(height: 50)
        .background(c.primary).foregroundColor(.white).cornerRadius(12)
        .disabled(isLoading)
    }

    func langName(_ code: String) -> String {
        switch code {
        case "en": return "English"
        case "es": return "Español"
        case "hi": return "हिन्दी"
        case "sw": return "Kiswahili"
        default: return code
        }
    }

    func loadProfile() {
        if let user = auth.user {
            name = user.name; email = user.email; phone = user.phone ?? ""; location = user.location ?? ""
        }
    }

    func saveProfile() async {
        isLoading = true; errorMessage = nil; successMessage = nil
        do {
            let data = ["name": name, "email": email, "phone": phone, "location": location]
            let response = try await APIService.shared.updateProfile(data)
            successMessage = response.message
        } catch { errorMessage = error.localizedDescription }
        isLoading = false
    }

    func changePassword() async {
        guard !currentPassword.isEmpty, !newPassword.isEmpty else { errorMessage = "All fields required"; return }
        guard newPassword == confirmPassword else { errorMessage = "Passwords do not match"; return }
        isLoading = true; errorMessage = nil; successMessage = nil
        do {
            let response = try await APIService.shared.changePassword(current: currentPassword, new: newPassword, confirm: confirmPassword)
            successMessage = response.message
            currentPassword = ""; newPassword = ""; confirmPassword = ""
        } catch { errorMessage = error.localizedDescription }
        isLoading = false
    }
}
