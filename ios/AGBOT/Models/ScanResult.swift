import Foundation

struct ScanResult: Codable {
    var status: String?
    var pestIdentified: String?
    var pestScientific: String?
    var confidence: Double?
    var damagePattern: String?
    var severity: String?
    var immediateAction: Bool?
    var treatments: Treatments?
    var scanId: Int?
    var message: String?
    // AI model fields
    var symptoms: [String]?
    var affectedPlants: [String]?
    var allPredictions: [PestPrediction]?
    // Text analysis fields
    var diseaseName: String?
    var scientificName: String?
    var description: String?
    var causes: [String]?
    var chemicalTreatments: [String]?
    var organicTreatments: [String]?
    var prevention: [String]?
    var userSymptoms: String?
    var plantType: String?

    enum CodingKeys: String, CodingKey {
        case status, confidence, severity, treatments, message, description, causes, prevention, symptoms
        case pestIdentified = "pest_identified"
        case pestScientific = "pest_scientific"
        case damagePattern = "damage_pattern"
        case immediateAction = "immediate_action"
        case scanId = "scan_id"
        case affectedPlants = "affected_plants"
        case allPredictions = "all_predictions"
        case diseaseName = "disease_name"
        case scientificName = "scientific_name"
        case chemicalTreatments = "chemical_treatments"
        case organicTreatments = "organic_treatments"
        case userSymptoms = "user_symptoms"
        case plantType = "plant_type"
    }

    var displayName: String {
        pestIdentified ?? diseaseName ?? "Unknown"
    }
    var displayScientific: String {
        pestScientific ?? scientificName ?? ""
    }
    var isHealthy: Bool {
        status == "Healthy" || pestIdentified == "None"
    }
}

struct PestPrediction: Codable {
    var pest: String
    var confidence: Double
}

struct Treatments: Codable {
    var immediate: [String]?
    var ipm: [String]?
    var prevention: [String]?
}

struct HistoryItem: Codable, Identifiable {
    var id: Int? = UUID().hashValue
    var plant: String?
    var pest: String?
    var pestIdentified: String?
    var date: String?
    var createdAt: String?
    var time: String?
    var severity: String?
    var cropType: String?
    var confidence: Double?

    enum CodingKeys: String, CodingKey {
        case id, plant, pest, date, time, severity, confidence
        case pestIdentified = "pest_identified"
        case createdAt = "created_at"
        case cropType = "crop_type"
    }

    var displayPest: String { pestIdentified ?? pest ?? "Unknown" }
    var displayPlant: String { plant ?? cropType ?? "Plant" }
    var displayDate: String { (createdAt ?? date ?? "").prefix(10).description }
}

struct HistoryResponse: Codable {
    let history: [HistoryItem]
    let stats: HistoryStats
}

struct HistoryStats: Codable {
    let totalScans: Int
    let pestsFound: Int
    let healthy: Int

    enum CodingKeys: String, CodingKey {
        case totalScans = "total_scans"
        case pestsFound = "pests_found"
        case healthy
    }
}
