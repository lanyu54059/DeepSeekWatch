import SwiftUI

@main
struct DeepSeekWatchApp: App {
    @StateObject private var configuration = Configuration()
    var body: some Scene {
        WindowGroup { ChatView().environmentObject(configuration) }
    }
}

struct ChatView: View {
    @StateObject private var chat = ChatStore()
    @State private var input = ""
    @State private var settings = false
    var body: some View {
        VStack(spacing: 5) {
            HStack {
                Text("✨ DeepSeek Watch").font(.caption2).lineLimit(1).minimumScaleFactor(0.7)
                Spacer(minLength: 0)
                Button { settings = true } label: { Image(systemName: "gearshape") }
                    .buttonStyle(.plain).accessibilityLabel("设置")
            }
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 8) {
                        if chat.messages.isEmpty { Text("你好，想聊些什么？").foregroundStyle(.secondary).font(.caption) }
                        ForEach(chat.messages) { message in
                            VStack(alignment: .leading, spacing: 3) {
                                Text(message.role == "user" ? "你" : "DeepSeek")
                                    .font(.caption2).foregroundStyle(message.role == "user" ? Color.gray : Color.cyan)
                                Text(message.content).font(.body).fixedSize(horizontal: false, vertical: true)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading).padding(8)
                            .background(message.role == "user" ? Color(white: 0.16) : Color(red: 0.03, green: 0.10, blue: 0.24))
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        if chat.loading { ProgressView("正在思考...").font(.caption) }
                        if let error = chat.error {
                            Text(error).foregroundStyle(.orange).font(.caption)
                            Button("重试") { chat.retry() }
                            Button("清空后重新提问") { chat.clear() }
                        }
                        Color.clear.frame(height: 1).id("bottom")
                    }
                }
                .onChange(of: chat.messages.count) { _, _ in withAnimation { proxy.scrollTo("bottom", anchor: .bottom) } }
                .onChange(of: chat.loading) { _, _ in withAnimation { proxy.scrollTo("bottom", anchor: .bottom) } }
            }
            HStack(spacing: 4) {
                TextField("输入问题...", text: $input).disabled(chat.loading || chat.error != nil)
                Button {
                    chat.send(input)
                    input = ""
                } label: { Image(systemName: "arrow.up.circle.fill").foregroundStyle(.blue).font(.title3) }
                .buttonStyle(.plain).accessibilityLabel("发送")
                .disabled(chat.loading || chat.error != nil || input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .padding(.horizontal, 5).background(Color.black)
        .sheet(isPresented: $settings) { WatchSettings(chat: chat) }
    }
}

struct WatchSettings: View {
    @EnvironmentObject private var configuration: Configuration
    @ObservedObject var chat: ChatStore
    @State private var key = ""
    @State private var confirmClear = false
    var body: some View {
        NavigationStack {
            Form {
                Section("API Key") {
                    Text(configuration.configured ? "已配置" : "未配置")
                    SecureField("备用：输入 Key", text: $key)
                    Button("保存到手表") { configuration.save(key); key = "" }
                        .disabled(key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    Button("清除手表 Key", role: .destructive) { configuration.save("") }
                    Text(configuration.status).font(.caption2)
                    if let error = configuration.error { Text(error).foregroundStyle(.orange) }
                }
                Picker("模型", selection: $chat.model) {
                    Text("Flash").tag("deepseek-flash")
                    Text("V4 Pro").tag("deepseek-v4-pro")
                }.disabled(chat.loading)
                Button("清空对话", role: .destructive) { confirmClear = true }
            }.navigationTitle("设置")
                .confirmationDialog("清空当前会话？", isPresented: $confirmClear) {
                    Button("清空", role: .destructive) { chat.clear() }
                }
        }
    }
}
