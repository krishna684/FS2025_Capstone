import Foundation
import UIKit

enum APIError: LocalizedError {
    case network(String)
    case server(String)
    case decoding(String)

    var errorDescription: String? {
        switch self {
        case .network(let msg): return msg
        case .server(let msg): return msg
        case .decoding(let msg): return msg
        }
    }
}

class APIService {
    static let shared = APIService()
    // Change to your computer's IP when testing on a physical device
    private let baseURL = "http://172.26.97.46:5001"

    private func getToken() -> String? {
        UserDefaults.standard.string(forKey: "jwt_token")
    }

    private func request<T: Decodable>(_ endpoint: String, method: String = "GET", body: Data? = nil) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.network("Invalid URL")
        }

        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = getToken() {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            req.httpBody = body
        }

        let (data, response) = try await URLSession.shared.data(for: req)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.network("No response")
        }

        if httpResponse.statusCode >= 400 {
            if let errorResp = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw APIError.server(errorResp.error)
            }
            throw APIError.server("Server error \(httpResponse.statusCode)")
        }

        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw APIError.decoding("Failed to parse response: \(error.localizedDescription)")
        }
    }

    // MARK: - Auth

    func login(email: String, password: String) async throws -> AuthResponse {
        let body = try JSONEncoder().encode(["email": email, "password": password])
        let response: AuthResponse = try await request("/api/auth/login", method: "POST", body: body)
        UserDefaults.standard.set(response.token, forKey: "jwt_token")
        return response
    }

    func register(name: String, email: String, phone: String, location: String, password: String) async throws -> AuthResponse {
        let payload: [String: String] = ["name": name, "email": email, "phone": phone, "location": location, "password": password]
        let body = try JSONEncoder().encode(payload)
        let response: AuthResponse = try await request("/api/auth/register", method: "POST", body: body)
        UserDefaults.standard.set(response.token, forKey: "jwt_token")
        return response
    }

    func getMe() async throws -> UserResponse {
        try await request("/api/auth/me")
    }

    func logout() {
        UserDefaults.standard.removeObject(forKey: "jwt_token")
    }

    // MARK: - Dashboard

    func getDashboard() async throws -> DashboardResponse {
        try await request("/api/dashboard")
    }

    // MARK: - Analysis

    func analyzeImage(_ image: UIImage) async throws -> ScanResult {
        guard let url = URL(string: "\(baseURL)/api/analyze") else {
            throw APIError.network("Invalid URL")
        }

        let boundary = UUID().uuidString
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        if let token = getToken() {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        var bodyData = Data()
        if let imageData = image.jpegData(compressionQuality: 0.8) {
            bodyData.append("--\(boundary)\r\n".data(using: .utf8)!)
            bodyData.append("Content-Disposition: form-data; name=\"image\"; filename=\"scan.jpg\"\r\n".data(using: .utf8)!)
            bodyData.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
            bodyData.append(imageData)
            bodyData.append("\r\n".data(using: .utf8)!)
        }
        bodyData.append("--\(boundary)--\r\n".data(using: .utf8)!)
        req.httpBody = bodyData

        let (data, response) = try await URLSession.shared.data(for: req)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode < 400 else {
            if let errorResp = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw APIError.server(errorResp.error)
            }
            throw APIError.server("Analysis failed")
        }
        return try JSONDecoder().decode(ScanResult.self, from: data)
    }

    func analyzeSymptoms(symptoms: String, plantType: String) async throws -> ScanResult {
        let payload = ["symptoms": symptoms, "plant_type": plantType]
        let body = try JSONEncoder().encode(payload)
        return try await request("/api/analyze_symptoms", method: "POST", body: body)
    }

    // MARK: - History

    func getHistory() async throws -> HistoryResponse {
        try await request("/api/history")
    }

    // MARK: - Settings

    func updateProfile(_ data: [String: String]) async throws -> MessageResponse {
        let body = try JSONEncoder().encode(data)
        return try await request("/api/profile", method: "PUT", body: body)
    }

    func updatePreferences(_ data: [String: String]) async throws -> MessageResponse {
        let body = try JSONEncoder().encode(data)
        return try await request("/api/preferences", method: "PUT", body: body)
    }

    func changePassword(current: String, new: String, confirm: String) async throws -> MessageResponse {
        let payload = ["current_password": current, "new_password": new, "confirm_password": confirm]
        let body = try JSONEncoder().encode(payload)
        return try await request("/api/security", method: "PUT", body: body)
    }
}
