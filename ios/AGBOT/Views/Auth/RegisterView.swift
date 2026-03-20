import SwiftUI

struct RegisterView: View {
    @EnvironmentObject var auth: AuthManager
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager
    @Environment(\.dismiss) var dismiss
    @State private var name = ""
    @State private var email = ""
    @State private var phone = ""
    @State private var location = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var isLoading = false
    @State private var errorMessage: String?

    var c: AppColors { themeManager.colors }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text(translations.t("register.title")).font(.title2.bold()).foregroundColor(c.text)
                Text(translations.t("register.subtitle")).font(.subheadline).foregroundColor(c.textSecondary)

                field("person", translations.t("register.fullname"), $name)
                field("envelope", translations.t("register.email"), $email, keyboard: .emailAddress)
                field("phone", translations.t("register.phone"), $phone, keyboard: .phonePad)
                field("location", translations.t("register.location"), $location)
                secureField("lock", translations.t("register.password"), $password)
                secureField("lock", translations.t("register.confirm"), $confirmPassword)

                if let error = errorMessage {
                    Text(error).font(.caption).foregroundColor(c.danger)
                }

                Button {
                    Task { await handleRegister() }
                } label: {
                    if isLoading { ProgressView().tint(.white) }
                    else { Text(translations.t("register.create")).fontWeight(.bold) }
                }
                .frame(maxWidth: .infinity).frame(height: 50)
                .background(c.primary).foregroundColor(.white).cornerRadius(12)
                .disabled(isLoading)

                HStack {
                    Text(translations.t("register.hasaccount")).foregroundColor(c.textSecondary)
                    Button(translations.t("register.signin")) { dismiss() }
                        .foregroundColor(c.primary).fontWeight(.bold)
                }.font(.subheadline)
            }
            .padding(24)
            .background(c.card).cornerRadius(16)
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(c.border))
            .padding(20)
        }
        .background(c.background.ignoresSafeArea())
        .navigationBarBackButtonHidden(false)
    }

    func field(_ icon: String, _ placeholder: String, _ text: Binding<String>, keyboard: UIKeyboardType = .default) -> some View {
        HStack {
            Image(systemName: icon).foregroundColor(c.textSecondary)
            TextField(placeholder, text: text).textInputAutocapitalization(keyboard == .emailAddress ? .never : .words).keyboardType(keyboard)
        }
        .padding(.horizontal, 14).frame(height: 48)
        .background(c.background).cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
    }

    func secureField(_ icon: String, _ placeholder: String, _ text: Binding<String>) -> some View {
        HStack {
            Image(systemName: icon).foregroundColor(c.textSecondary)
            SecureField(placeholder, text: text)
        }
        .padding(.horizontal, 14).frame(height: 48)
        .background(c.background).cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
    }

    func handleRegister() async {
        guard !name.isEmpty, !email.isEmpty, !password.isEmpty else { errorMessage = "Name, email, and password required"; return }
        guard password == confirmPassword else { errorMessage = "Passwords do not match"; return }
        isLoading = true; errorMessage = nil
        do { try await auth.register(name: name, email: email, phone: phone, location: location, password: password) }
        catch { errorMessage = error.localizedDescription }
        isLoading = false
    }
}
