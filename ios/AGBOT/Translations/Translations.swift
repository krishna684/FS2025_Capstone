import Foundation
import SwiftUI

@MainActor
class TranslationManager: ObservableObject {
    @AppStorage("appLanguage") var currentLanguage = "en"

    private let translations: [String: [String: Any]] = {
        var result: [String: [String: Any]] = [:]
        for lang in ["en", "es", "hi", "sw"] {
            if let url = Bundle.main.url(forResource: lang, withExtension: "json"),
               let data = try? Data(contentsOf: url),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                result[lang] = json
            }
        }
        // Fallback hardcoded English
        if result.isEmpty {
            result["en"] = TranslationManager.fallbackEnglish
        }
        return result
    }()

    func t(_ key: String) -> String {
        let keys = key.split(separator: ".").map(String.init)
        var value: Any? = translations[currentLanguage] ?? translations["en"]
        for k in keys {
            if let dict = value as? [String: Any] {
                value = dict[k]
            } else {
                // Fallback to English
                var fb: Any? = translations["en"]
                for fk in keys { if let d = fb as? [String: Any] { fb = d[fk] } }
                return (fb as? String) ?? key
            }
        }
        return (value as? String) ?? key
    }

    func setLanguage(_ lang: String) {
        currentLanguage = lang
        objectWillChange.send()
    }

    static let fallbackEnglish: [String: Any] = [
        "brand": ["name": "AGBOT", "tagline": "From Data to Harvest - Smarter Solutions for Farmers"],
        "nav": ["home": "Home", "dashboard": "Dashboard", "scan": "Scan", "describe": "Describe", "history": "History", "settings": "Settings", "help": "Help", "about": "About", "logout": "Logout"],
        "login": ["title": "Welcome Back", "subtitle": "Sign in to continue to AGBOT", "email": "Email or Phone", "password": "Password", "signin": "Sign In", "noaccount": "Don't have an account?", "signup": "Sign up"],
        "register": ["title": "Create Account", "subtitle": "Join AGBOT today", "fullname": "Full Name", "email": "Email Address", "phone": "Phone Number", "location": "Location", "password": "Password", "confirm": "Confirm Password", "create": "Create Account", "hasaccount": "Already have an account?", "signin": "Sign in"],
        "dashboard": ["welcome": "Welcome Back!", "greeting": "Hi, Farmer!", "scanButton": "Scan New Leaf", "totalScans": "Total Scans", "healthRate": "Health Rate", "pestsFound": "Pests Found", "aiAccuracy": "AI Accuracy", "healthyPlants": "Healthy Plants", "pestsDetected": "Pests Detected", "recentDetections": "Recent Detections", "viewAll": "View All", "pestTrends": "Pest Detection Trends", "healthDist": "Health Distribution", "plantHealthDist": "Plant Health Distribution", "healthy": "Healthy", "pestDamage": "Pest Damage", "disease": "Disease", "critical": "Critical", "quickActions": "Quick Actions", "scanNewLeaf": "Scan New Leaf", "viewHistory": "View History", "exportReport": "Export Report"],
        "scan": ["title": "Scan Plant", "subtitle": "Take or select a photo of the affected plant", "upload": "Upload Image", "camera": "Camera", "gallery": "Gallery", "noimage": "No image selected", "analyze": "Analyze Image", "analyzing": "Analyzing..."],
        "describe": ["title": "Describe Symptoms", "subtitle": "Tell us what you see on your plant", "plantType": "Plant Type", "symptoms": "Describe the symptoms", "analyze": "Analyze Symptoms"],
        "results": ["title": "Results", "detected": "Pest Detected", "confidence": "Confidence", "severity": "Severity", "crop": "Crop", "field": "Field", "immediate": "Immediate Actions", "shortTerm": "Short-Term Treatment", "longTerm": "Long-Term Prevention", "preventive": "Preventive Measures", "prevention": "Prevention", "newscan": "New Scan"],
        "history": ["title": "Scan History", "search": "Search by plant or pest...", "empty": "No scans found", "totalScans": "Total Scans", "pestsFound": "Pests Found", "noResults": "No scans found", "searchby": "Search by plant or pest..."],
        "settings": ["title": "Settings", "profile": "Profile", "preferences": "Preferences", "security": "Security", "save": "Save Changes", "name": "Full Name", "fullName": "Full Name", "email": "Email Address", "phone": "Phone Number", "location": "Location", "farmName": "Farm Name", "farmSize": "Farm Size", "darkMode": "Dark Mode", "lightMode": "Light Mode", "language": "Language", "currentPassword": "Current Password", "newPassword": "New Password", "confirmPassword": "Confirm Password", "changePassword": "Change Password"],
        "about": ["mission": "Our Mission", "impact": "Our Impact", "team": "Our Team"],
        "help": ["title": "Help Center", "subtitle": "Learn how to use AGBOT effectively", "quickStart": "Quick Start Guide", "step1Title": "Capture or Upload", "step1Desc": "Take a photo of your plant leaf or upload an existing image.", "step2Title": "AI Analysis", "step2Desc": "Our AI analyzes the image to detect pests and diseases.", "step3Title": "Get Recommendations", "step3Desc": "Receive detailed treatment recommendations and prevention tips.", "faq": "FAQ", "tips": "Pro Tips"],
        "common": ["error": "Error", "success": "Success"]
    ]
}
