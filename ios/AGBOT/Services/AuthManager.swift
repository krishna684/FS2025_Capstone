import Foundation
import SwiftUI

@MainActor
class AuthManager: ObservableObject {
    @Published var user: User?
    @Published var isLoggedIn = false
    @Published var isLoading = true

    init() {
        Task { await checkAuth() }
    }

    func checkAuth() async {
        if UserDefaults.standard.string(forKey: "jwt_token") != nil {
            do {
                let response = try await APIService.shared.getMe()
                self.user = response.user
                self.isLoggedIn = true
            } catch {
                logout()
            }
        }
        isLoading = false
    }

    func login(email: String, password: String) async throws {
        let response = try await APIService.shared.login(email: email, password: password)
        self.user = response.user
        self.isLoggedIn = true
    }

    func register(name: String, email: String, phone: String, location: String, password: String) async throws {
        let response = try await APIService.shared.register(name: name, email: email, phone: phone, location: location, password: password)
        self.user = response.user
        self.isLoggedIn = true
    }

    func logout() {
        APIService.shared.logout()
        self.user = nil
        self.isLoggedIn = false
    }

    func refreshUser() async {
        do {
            let response = try await APIService.shared.getMe()
            self.user = response.user
        } catch {}
    }
}
