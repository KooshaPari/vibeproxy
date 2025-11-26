import Foundation

// Model structure for service models
struct ModelInfo: Codable {
    let name: String
    let displayName: String?
    let description: String?
    let maxTokens: Int?
    let contextWindow: Int?
    let supportsStreaming: Bool?
}

// Service info structure for service discovery
struct ServiceDiscoveryInfo: Codable {
    let id: String
    let name: String
    let displayName: String
    let icon: String?
    let provider: String
    let isConfigBased: Bool
    let modelCount: Int
    let available: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case displayName = "display_name"
        case icon
        case provider
        case isConfigBased = "is_config_based"
        case modelCount = "model_count"
        case available
    }
}

// Wrapper for services response
struct ServicesResponse: Codable {
    let services: [ServiceDiscoveryInfo]
    let count: Int
}

// Result type for model discovery
enum ModelDiscoveryResult {
    case success([ModelInfo])
    case failure(Error)
}

// Result type for service discovery
enum ServiceDiscoveryResult {
    case success([ServiceDiscoveryInfo])
    case failure(Error)
}

// CLI Proxy API client for model discovery
class CLIProxyAPI {
    static let shared = CLIProxyAPI()
    
    private let baseURL = "http://localhost:8318"
    private let session = URLSession.shared
    
    private init() {}
    
    /// Get available models for a specific service
    func getAvailableModels(for service: String, completion: @escaping (ModelDiscoveryResult) -> Void) {
        let endpoint = "\(baseURL)/api/services/\(service)/models"
        guard let url = URL(string: endpoint) else {
            let error = NSError(domain: "CLIProxyAPI", code: 400, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
            completion(.failure(error))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10.0
        
        let task = session.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    let error = NSError(domain: "CLIProxyAPI", code: 500, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
                    completion(.failure(error))
                    return
                }
                
                if httpResponse.statusCode == 200 {
                    if let data = data {
                        do {
                            let decoder = JSONDecoder()
                            let models = try decoder.decode([ModelInfo].self, from: data)
                            completion(.success(models))
                        } catch {
                            completion(.failure(error))
                        }
                    } else {
                        let models = self.getFallbackModels(for: service)
                        completion(.success(models))
                    }
                } else {
                    // Try fallback models for common services
                    let fallbackModels = self.getFallbackModels(for: service)
                    completion(.success(fallbackModels))
                }
            }
        }
        
        task.resume()
    }
    
    /// Get fallback models when API is not available
    private func getFallbackModels(for service: String) -> [ModelInfo] {
        switch service.lowercased() {
        case "claude":
            return [
                ModelInfo(name: "claude-haiku-4-5-20251001", 
                         displayName: "Claude 4.5 Haiku", 
                         description: "Fast, lightweight Claude model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "claude-sonnet-4-5-20250929", 
                         displayName: "Claude 4.5 Sonnet", 
                         description: "Advanced reasoning Claude model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "claude-opus-4-1-20250805", 
                         displayName: "Claude 4.1 Opus", 
                         description: "Most powerful Claude model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "claude-opus-4-20250514", 
                         displayName: "Claude 4 Opus", 
                         description: "Previous generation powerful Claude model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "claude-sonnet-4-20250514", 
                         displayName: "Claude 4 Sonnet", 
                         description: "Balanced performance Claude model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "claude-3-7-sonnet-20250219", 
                         displayName: "Claude 3.7 Sonnet", 
                         description: "Previous generation advanced Claude model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "claude-3-5-haiku-20241022", 
                         displayName: "Claude 3.5 Haiku", 
                         description: "Previous generation lightweight Claude model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true)
            ]
        case "openai", "codex":
            return [
                ModelInfo(name: "gpt-4o", 
                         displayName: "GPT-4o", 
                         description: "Most capable model with vision and audio", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "gpt-4o-mini", 
                         displayName: "GPT-4o Mini", 
                         description: "Fast and cost-effective with vision", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "gpt-4-turbo", 
                         displayName: "GPT-4 Turbo", 
                         description: "Latest GPT-4 model with function calling", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "gpt-3.5-turbo", 
                         displayName: "GPT-3.5 Turbo", 
                         description: "Fast and affordable for simple tasks", 
                         maxTokens: 16385,
                         contextWindow: 16385,
                         supportsStreaming: true)
            ]
        case "gemini":
            return [
                ModelInfo(name: "gemini-1.5-pro", 
                         displayName: "Gemini 1.5 Pro", 
                         description: "Most capable Gemini model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "gemini-1.5-flash", 
                         displayName: "Gemini 1.5 Flash", 
                         description: "Fast and efficient model", 
                         maxTokens: 100000,
                         contextWindow: 100000,
                         supportsStreaming: true),
                ModelInfo(name: "gemini-pro", 
                         displayName: "Gemini Pro", 
                         description: "Previous generation high-quality model", 
                         maxTokens: 32000,
                         contextWindow: 32000,
                         supportsStreaming: true)
            ]
        case "qwen":
            return [
                ModelInfo(name: "qwen-max", 
                         displayName: "Qwen Max", 
                         description: "Most capable Qwen model", 
                         maxTokens: 8192,
                         contextWindow: 8192,
                         supportsStreaming: true),
                ModelInfo(name: "qwen-plus", 
                         displayName: "Qwen Plus", 
                         description: "Balanced performance and cost", 
                         maxTokens: 8192,
                         contextWindow: 8192,
                         supportsStreaming: true),
                ModelInfo(name: "qwen-turbo", 
                         displayName: "Qwen Turbo", 
                         description: "Fast and cost-effective", 
                         maxTokens: 8192,
                         contextWindow: 8192,
                         supportsStreaming: true)
            ]
        case "auggie":
            return [
                ModelInfo(name: "auggie-haiku4.5", 
                         displayName: "Auggie Claude Haiku 4.5", 
                         description: "Anthropic Claude Haiku 4.5", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: false),
                ModelInfo(name: "auggie-sonnet4", 
                         displayName: "Auggie Claude Sonnet 4", 
                         description: "Anthropic Claude Sonnet 4", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: false),
                ModelInfo(name: "auggie-sonnet4.5", 
                         displayName: "Auggie Claude Sonnet 4.5", 
                         description: "Anthropic Claude Sonnet 4.5", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: false),
                ModelInfo(name: "auggie-gpt5", 
                         displayName: "Auggie GPT-5", 
                         description: "OpenAI GPT-5 legacy", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: false),
                ModelInfo(name: "auggie-gpt5.1", 
                         displayName: "Auggie GPT-5.1", 
                         description: "OpenAI GPT-5.1", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: false)
            ]
        case "cursor":
            return [
                ModelInfo(name: "cursor-auto", 
                         displayName: "Cursor Agent (Auto)", 
                         description: "Automatic model selection", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-composer-1", 
                         displayName: "Composer 1", 
                         description: "Cursor's Composer model", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-sonnet-4.5", 
                         displayName: "Claude Sonnet 4.5", 
                         description: "Anthropic Claude Sonnet 4.5", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-sonnet-4.5-thinking", 
                         displayName: "Claude Sonnet 4.5 Thinking", 
                         description: "Claude Sonnet 4.5 with thinking", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gemini-3-pro", 
                         displayName: "Gemini 3 Pro", 
                         description: "Google Gemini 3 Pro", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5", 
                         displayName: "GPT-5", 
                         description: "OpenAI GPT-5", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5.1", 
                         displayName: "GPT-5.1", 
                         description: "OpenAI GPT-5.1", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5-high", 
                         displayName: "GPT-5 High", 
                         description: "OpenAI GPT-5 with high context", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5.1-high", 
                         displayName: "GPT-5.1 High", 
                         description: "OpenAI GPT-5.1 with high context", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5-codex", 
                         displayName: "GPT-5 Codex", 
                         description: "OpenAI GPT-5 Codex for code", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5-codex-high", 
                         displayName: "GPT-5 Codex High", 
                         description: "OpenAI GPT-5 Codex with high context", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5.1-codex", 
                         displayName: "GPT-5.1 Codex", 
                         description: "OpenAI GPT-5.1 Codex for code", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-gpt-5.1-codex-high", 
                         displayName: "GPT-5.1 Codex High", 
                         description: "OpenAI GPT-5.1 Codex with high context", 
                         maxTokens: 128000,
                         contextWindow: 128000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-opus-4.1", 
                         displayName: "Claude Opus 4.1", 
                         description: "Anthropic Claude Opus 4.1", 
                         maxTokens: 200000,
                         contextWindow: 200000,
                         supportsStreaming: true),
                ModelInfo(name: "cursor-grok", 
                         displayName: "Grok", 
                         description: "xAI Grok", 
                         maxTokens: 100000,
                         contextWindow: 100000,
                         supportsStreaming: true)
            ]
        default:
            return [
                ModelInfo(name: "default", 
                         displayName: "Default Model", 
                         description: "Generic model for unknown services", 
                         maxTokens: 4096,
                         contextWindow: 4096,
                         supportsStreaming: true)
            ]
        }
    }
    
    /// Get all available services
    func getAvailableServices(completion: @escaping (ServiceDiscoveryResult) -> Void) {
        let endpoint = "\(baseURL)/api/v1/services"
        guard let url = URL(string: endpoint) else {
            let error = NSError(domain: "CLIProxyAPI", code: 400, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])
            completion(.failure(error))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10.0
        
        let task = session.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    let error = NSError(domain: "CLIProxyAPI", code: 500, userInfo: [NSLocalizedDescriptionKey: "Invalid response"])
                    completion(.failure(error))
                    return
                }
                
                if httpResponse.statusCode == 200, let data = data {
                    do {
                        let decoder = JSONDecoder()
                        let response = try decoder.decode(ServicesResponse.self, from: data)
                        completion(.success(response.services))
                    } catch {
                        completion(.failure(error))
                    }
                } else {
                    let error = NSError(domain: "CLIProxyAPI", code: httpResponse.statusCode, userInfo: [NSLocalizedDescriptionKey: "Failed to fetch services"])
                    completion(.failure(error))
                }
            }
        }
        
        task.resume()
    }
    
    /// Get a specific service by ID
    func getService(id: String, completion: @escaping (ServiceDiscoveryInfo?) -> Void) {
        let endpoint = "\(baseURL)/api/v1/services/\(id)"
        guard let url = URL(string: endpoint) else {
            completion(nil)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10.0
        
        let task = session.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    print("Failed to fetch service \(id): \(error)")
                    completion(nil)
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200, let data = data else {
                    completion(nil)
                    return
                }
                
                do {
                    let decoder = JSONDecoder()
                    let service = try decoder.decode(ServiceDiscoveryInfo.self, from: data)
                    completion(service)
                } catch {
                    print("Failed to decode service \(id): \(error)")
                    completion(nil)
                }
            }
        }
        
        task.resume()
    }
    
    /// Check if the CLI Proxy API is running
    func isAPIAvailable(completion: @escaping (Bool) -> Void) {
        let endpoint = "\(baseURL)/api/health"
        guard let url = URL(string: endpoint) else {
            completion(false)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 3.0
        
        let task = session.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    print("CLI Proxy API health check failed: \(error)")
                    completion(false)
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    completion(false)
                    return
                }
                
                completion(httpResponse.statusCode == 200)
            }
        }
        
        task.resume()
    }
}
