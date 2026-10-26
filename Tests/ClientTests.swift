import Foundation

final class MockProtocol: URLProtocol {
    static var status = 200
    static var body = Data()
    static var networkError: URLError?
    static var requestCheck: ((URLRequest) throws -> Void)?
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        do { try Self.requestCheck?(request) }
        catch { client?.urlProtocol(self, didFailWithError: error); return }
        if let error = Self.networkError { client?.urlProtocol(self, didFailWithError: error); return }
        client?.urlProtocol(self, didReceive: HTTPURLResponse(url: request.url!, statusCode: Self.status, httpVersion: nil, headerFields: nil)!, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Self.body)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}

@main
struct ClientTests {
    static func main() async throws {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockProtocol.self]
        let client = DeepSeekClient(session: URLSession(configuration: config))
        let messages = [APIMessage(role: "user", content: "你好"), APIMessage(role: "assistant", content: "你好！"), APIMessage(role: "user", content: "继续")]
        // Synthetic test credential; never a real API key.
        MockProtocol.requestCheck = { request in
            precondition(request.httpMethod == "POST")
            precondition(request.url?.absoluteString == "https://api.deepseek.com/chat/completions")
            precondition(request.value(forHTTPHeaderField: "Authorization") == "Bearer TEST_ONLY")
        }
        let encoded = try JSONEncoder().encode(DeepSeekClient.Request(model: "deepseek-flash", messages: messages))
        let object = try JSONSerialization.jsonObject(with: encoded) as! [String: Any]
        precondition((object["messages"] as! [[String: String]]).count == 3)
        precondition(object["stream"] as? Bool == false && object["max_tokens"] as? Int == 4096)
        MockProtocol.body = Data(#"{"choices":[{"message":{"content":"中文回答"},"finish_reason":"stop"}]}"#.utf8)
        let reply = try await client.reply(messages: messages, model: "deepseek-flash", key: "TEST_ONLY")
        precondition(reply == "中文回答")
        for status in [401, 402, 403, 429, 500, 503, 400] {
            MockProtocol.status = status
            do { _ = try await client.reply(messages: messages, model: "deepseek-flash", key: "TEST_ONLY"); fatalError("Expected HTTP failure") }
            catch let error as DeepSeekClient.Failure { precondition(error.message == DeepSeekClient.failure(status: status).message) }
        }
        MockProtocol.status = 200
        for body in ["bad-json", #"{"choices":[]}"#, #"{"choices":[{"message":{"content":null}}]}"#] {
            MockProtocol.body = Data(body.utf8)
            do { _ = try await client.reply(messages: messages, model: "deepseek-flash", key: "TEST_ONLY"); fatalError("Expected parsing/empty failure") }
            catch is DeepSeekClient.Failure {}
        }
        for code in [URLError.timedOut, .notConnectedToInternet] {
            MockProtocol.networkError = URLError(code)
            do { _ = try await client.reply(messages: messages, model: "deepseek-flash", key: "TEST_ONLY"); fatalError("Expected network failure") }
            catch is DeepSeekClient.Failure {}
        }
        do { _ = try await client.reply(messages: messages, model: "deepseek-flash", key: ""); fatalError("Expected missing key failure") }
        catch is DeepSeekClient.Failure {}
        print("PASS: API request, context, Chinese response, HTTP errors, parsing, empty response, timeout, offline and missing key")
    }
}
