import Foundation

struct APIMessage: Codable, Equatable {
    let role: String
    let content: String
}

struct DeepSeekClient {
    struct Request: Encodable {
        let model: String
        let messages: [APIMessage]
        let max_tokens = 4096
        let stream = false
        let thinking = ["type": "disabled"]
    }
    struct Response: Decodable {
        struct Choice: Decodable {
            struct Message: Decodable { let content: String? }
            let message: Message
            let finish_reason: String?
        }
        let choices: [Choice]
    }
    struct Failure: LocalizedError {
        let message: String
        var errorDescription: String? { message }
    }
    var session: URLSession = .shared

    func reply(messages: [APIMessage], model: String, key: String) async throws -> String {
        guard !key.isEmpty else { throw Failure(message: "请先在设置中配置 API Key。") }
        var request = URLRequest(url: URL(string: "https://api.deepseek.com/chat/completions")!)
        request.httpMethod = "POST"
        request.timeoutInterval = 120
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(key)", forHTTPHeaderField: "Authorization")
        request.httpBody = try JSONEncoder().encode(Request(model: model, messages: messages))
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else { throw Failure(message: "服务器响应无效。") }
            guard (200..<300).contains(http.statusCode) else { throw Self.failure(status: http.statusCode) }
            let decoded: Response
            do { decoded = try JSONDecoder().decode(Response.self, from: data) }
            catch { throw Failure(message: "回复解析失败，请重试。") }
            guard let choice = decoded.choices.first,
                  let content = choice.message.content?.trimmingCharacters(in: .whitespacesAndNewlines),
                  !content.isEmpty else { throw Failure(message: "收到空回复，请重试。") }
            return content + (choice.finish_reason == "length" ? "\n\n（已达到回答长度上限，可继续追问。）" : "")
        } catch let error as URLError {
            if error.code == .cancelled { throw CancellationError() }
            throw Failure(message: error.code == .timedOut ? "请求超时，请重试。" : "网络不可用，请检查手表或配对 iPhone 的网络。")
        }
    }

    static func failure(status: Int) -> Failure {
        let message: String
        switch status {
        case 401: message = "API Key 无效，请重新配置。"
        case 402: message = "账户余额不足，请检查 DeepSeek 账户。"
        case 403: message = "账户无权访问，请检查账户状态。"
        case 429: message = "请求过于频繁，请稍后重试。"
        case 500...599: message = "DeepSeek 服务暂时不可用，请稍后重试。"
        default: message = "请求失败（HTTP \(status)），请检查模型和账户配置。"
        }
        return Failure(message: message)
    }
}
