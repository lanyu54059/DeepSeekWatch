import Foundation
import Combine

struct ChatMessage: Identifiable {
    let id = UUID()
    let role: String
    let content: String
}

@MainActor
final class ChatStore: ObservableObject {
    @Published private(set) var messages: [ChatMessage] = []
    @Published private(set) var loading = false
    @Published private(set) var error: String?
    @Published var model = "deepseek-flash"
    private var task: Task<Void, Never>?
    private var generation = UUID()

    func send(_ input: String) {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !loading, !text.isEmpty, error == nil else { return }
        messages.append(ChatMessage(role: "user", content: text))
        request()
    }
    func retry() {
        guard !loading, error != nil, messages.last?.role == "user" else { return }
        request()
    }
    func clear() {
        generation = UUID()
        task?.cancel()
        task = nil
        messages = []
        error = nil
        loading = false
    }
    private func request() {
        loading = true
        error = nil
        let token = generation
        // Keep complete recent user/assistant pairs, plus the pending question.
        let context = [APIMessage(role: "system", content: "你是 Apple Watch 上的中文助手。默认简洁作答，适合小屏阅读；用户明确要求详细解释时可以展开。使用纯文本。")]
            + messages.suffix(13).map { APIMessage(role: $0.role, content: $0.content) }
        let selectedModel = model
        task = Task {
            defer { if generation == token { loading = false; task = nil } }
            do {
                let reply = try await DeepSeekClient().reply(messages: context, model: selectedModel, key: Keychain.read())
                guard !Task.isCancelled, generation == token else { return }
                messages.append(ChatMessage(role: "assistant", content: reply))
            } catch is CancellationError {} catch {
                guard generation == token else { return }
                self.error = error.localizedDescription
            }
        }
    }
}
