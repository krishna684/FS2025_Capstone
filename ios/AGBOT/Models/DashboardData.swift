import Foundation

struct DashboardResponse: Codable {
    let userData: UserStats
    let recentDetections: [Detection]
    let pestTrends: PestTrends
    let weeklyChange: String
    let monthlyChange: String
    let weather: Weather
    let healthDistribution: HealthDistribution
    let currentDate: String

    enum CodingKeys: String, CodingKey {
        case userData = "user_data"
        case recentDetections = "recent_detections"
        case pestTrends = "pest_trends"
        case weeklyChange = "weekly_change"
        case monthlyChange = "monthly_change"
        case weather
        case healthDistribution = "health_distribution"
        case currentDate = "current_date"
    }
}

struct UserStats: Codable {
    let totalScans: Int
    let healthyPercentage: Int
    let pestsDetected: Int
    let aiAccuracy: Int

    enum CodingKeys: String, CodingKey {
        case totalScans = "total_scans"
        case healthyPercentage = "healthy_percentage"
        case pestsDetected = "pests_detected"
        case aiAccuracy = "ai_accuracy"
    }
}

struct Detection: Codable, Identifiable {
    let id: Int
    let pest: String
    let crop: String
    let field: String
    let severity: String
    let percentage: Int
    let date: String
    let time: String
}

struct PestTrends: Codable {
    let months: [String]
    let values: [Int]
}

struct Weather: Codable {
    let temperature: Int
    let condition: String
    let humidity: Int
}

struct HealthDistribution: Codable {
    let healthy: Int
    let pestDamage: Int
    let disease: Int
    let critical: Int

    enum CodingKeys: String, CodingKey {
        case healthy
        case pestDamage = "pest_damage"
        case disease, critical
    }
}
