import SwiftUI

struct LoginView: View {
    @EnvironmentObject var auth: AuthManager
    @EnvironmentObject var themeManager: ThemeManager
    @EnvironmentObject var translations: TranslationManager
    @State private var email = ""
    @State private var password = ""
    @State private var showPassword = false
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showRegister = false

    var c: AppColors { themeManager.colors }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Logo
                    VStack(spacing: 8) {
                        Circle()
                            .fill(c.primary.opacity(0.15))
                            .frame(width: 88, height: 88)
                            .overlay(Image(systemName: "leaf.fill").font(.system(size: 40)).foregroundColor(c.primary))
                        Text("AGBOT").font(.system(size: 32, weight: .heavy)).foregroundColor(c.primary)
                        Text("From Data to Harvest").font(.subheadline).foregroundColor(c.textSecondary)
                    }.padding(.top, 40)

                    // Form
                    VStack(spacing: 20) {
                        Text(translations.t("login.title")).font(.title2.bold()).foregroundColor(c.text)
                        Text(translations.t("login.subtitle")).font(.subheadline).foregroundColor(c.textSecondary)

                        VStack(alignment: .leading, spacing: 6) {
                            Text(translations.t("login.email")).font(.caption.bold()).foregroundColor(c.textSecondary)
                            HStack {
                                Image(systemName: "envelope").foregroundColor(c.textSecondary)
                                TextField(translations.t("login.email"), text: $email)
                                    .textInputAutocapitalization(.never).keyboardType(.emailAddress)
                            }
                            .padding(.horizontal, 14).frame(height: 48)
                            .background(c.background).cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text(translations.t("login.password")).font(.caption.bold()).foregroundColor(c.textSecondary)
                            HStack {
                                Image(systemName: "lock").foregroundColor(c.textSecondary)
                                if showPassword {
                                    TextField(translations.t("login.password"), text: $password)
                                } else {
                                    SecureField(translations.t("login.password"), text: $password)
                                }
                                Button { showPassword.toggle() } label: {
                                    Image(systemName: showPassword ? "eye.slash" : "eye").foregroundColor(c.textSecondary)
                                }
                            }
                            .padding(.horizontal, 14).frame(height: 48)
                            .background(c.background).cornerRadius(12)
                            .overlay(RoundedRectangle(cornerRadius: 12).stroke(c.border))
                        }

                        if let error = errorMessage {
                            Text(error).font(.caption).foregroundColor(c.danger)
                        }

                        Button {
                            Task { await handleLogin() }
                        } label: {
                            if isLoading {
                                ProgressView().tint(.white)
                            } else {
                                Text(translations.t("login.signin")).fontWeight(.bold)
                            }
                        }
                        .frame(maxWidth: .infinity).frame(height: 50)
                        .background(c.primary).foregroundColor(.white).cornerRadius(12)
                        .disabled(isLoading)

                        HStack {
                            Text(translations.t("login.noaccount")).foregroundColor(c.textSecondary)
                            Button(translations.t("login.signup")) { showRegister = true }
                                .foregroundColor(c.primary).fontWeight(.bold)
                        }.font(.subheadline)
                    }
                    .padding(24)
                    .background(c.card)
                    .cornerRadius(16)
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(c.border))
                }
                .padding(20)
            }
            .background(c.background.ignoresSafeArea())
            .navigationDestination(isPresented: $showRegister) {
                RegisterView()
            }
        }
    }

    func handleLogin() async {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Please enter email and password"; return
        }
        isLoading = true; errorMessage = nil
        do {
            try await auth.login(email: email, password: password)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
