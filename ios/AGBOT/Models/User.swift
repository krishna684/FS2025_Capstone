import Foundation

struct User: Codable, Identifiable {
    let id: Int
    let email: String
    let name: String
    var phone: String?
    var location: String?
    var language: String?
    var units: String?
    var theme: String?
    var farmName: String?
    var farmSize: String?
    var crops: String?
    var notificationEmail: Bool?
    var notificationPush: Bool?
    var createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, email, name, phone, location, language, units, theme, crops
        case farmName = "farm_name"
        case farmSize = "farm_size"
        case notificationEmail = "notification_email"
        case notificationPush = "notification_push"
        case createdAt = "created_at"
    }
}

struct AuthResponse: Codable {
    let token: String
    let user: User
    var message: String?
}

struct UserResponse: Codable {
    let user: User
}

struct MessageResponse: Codable {
    let message: String
}

struct ErrorResponse: Codable {
    let error: String
}
