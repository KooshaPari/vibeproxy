import Foundation

// GatewayProvider represents a custom LLM provider configuration
struct GatewayProvider: Codable, Identifiable {
    let id: String
    var name: String
    var type: String
    var baseURL: String
    var apiKey: String
    var headers: [String: String]?
    var models: [GatewayProviderModel]?

    enum CodingKeys: String, CodingKey {
        case name
        case type
        case baseURL = "base-url"
        case apiKey = "api-key"
        case headers
        case models
    }

    init(name: String, type: String, baseURL: String, apiKey: String, headers: [String: String]? = nil, models: [GatewayProviderModel]? = nil) {
        self.id = UUID().uuidString
        self.name = name
        self.type = type
        self.baseURL = baseURL
        self.apiKey = apiKey
        self.headers = headers
        self.models = models
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = UUID().uuidString
        self.name = try container.decode(String.self, forKey: .name)
        self.type = try container.decode(String.self, forKey: .type)
        self.baseURL = try container.decode(String.self, forKey: .baseURL)
        self.apiKey = try container.decode(String.self, forKey: .apiKey)
        self.headers = try container.decodeIfPresent([String: String].self, forKey: .headers)
        self.models = try container.decodeIfPresent([GatewayProviderModel].self, forKey: .models)
    }
}

// GatewayProviderModel represents a model mapping for a provider
struct GatewayProviderModel: Codable {
    var name: String
    var alias: String
}

// Provider type options
enum ProviderType: String, CaseIterable {
    case openai = "openai"
    case anthropic = "anthropic"
    case ollama = "ollama"
    case bedrock = "bedrock"
    case cohere = "cohere"
    case custom = "custom"

    var displayName: String {
        switch self {
        case .openai:
            return "OpenAI"
        case .anthropic:
            return "Anthropic"
        case .ollama:
            return "Ollama"
        case .bedrock:
            return "AWS Bedrock"
        case .cohere:
            return "Cohere"
        case .custom:
            return "Custom"
        }
    }
}
