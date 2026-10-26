import SwiftUI

@main
struct DeepSeekPhoneApp: App {
    @StateObject private var configuration = Configuration()
    @State private var key = ""
    var body: some Scene {
        WindowGroup {
            NavigationStack {
                Form {
                    Section("DeepSeek API Key") {
                        SecureField("输入 API Key", text: $key)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                        Text(configuration.configured ? "本机已配置" : "本机尚未配置")
                        Button("保存") { configuration.save(key); key = "" }
                            .disabled(key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        Button("同步到 Apple Watch") { configuration.sync() }
                            .disabled(!configuration.configured)
                        Button("清除 iPhone 密钥", role: .destructive) { configuration.save("") }
                    }
                    Section("连接与同步状态") {
                        Text(configuration.status)
                        if let error = configuration.error { Text(error).foregroundStyle(.red) }
                    }
                    Section {
                        Text("聊天和网络请求在手表上运行。保存后点击同步；离线时等待手表连接。清除本机密钥不会清除另一设备，请分别操作。")
                    }
                }.navigationTitle("DeepSeek Watch")
            }
        }
    }
}
