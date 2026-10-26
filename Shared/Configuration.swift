import Foundation
import Combine
import WatchConnectivity

final class Configuration: NSObject, ObservableObject, WCSessionDelegate {
    @Published private(set) var configured = false
    @Published private(set) var status = "正在连接…"
    @Published var error: String?
    private var session: WCSession?

    override init() {
        super.init()
        refresh()
        if WCSession.isSupported() {
            session = .default
            session?.delegate = self
            session?.activate()
        } else { status = "此设备不支持配置同步" }
    }

    func refresh() {
        do { configured = try !Keychain.read().isEmpty }
        catch { self.error = error.localizedDescription }
    }

    func save(_ key: String) {
        do {
            try Keychain.save(key.trimmingCharacters(in: .whitespacesAndNewlines))
            refresh()
            status = configured ? "已保存到本机钥匙串" : "已清除本机密钥"
            error = nil
        } catch { self.error = error.localizedDescription }
    }

    func sync() {
        guard let session, session.activationState == .activated else {
            status = "连接尚未就绪，请稍后重试"; return
        }
        #if os(iOS)
        guard session.isPaired, session.isWatchAppInstalled else {
            status = "请先配对手表并安装 Watch App"; return
        }
        #endif
        do {
            let key = try Keychain.read()
            guard !key.isEmpty else { status = "请先保存 API Key"; return }
            // Latest-only queued configuration; never use UserDefaults or logs.
            try session.updateApplicationContext(["apiKey": key])
            status = "配置已排队，等待手表接收；尚未确认保存"
            if session.isReachable {
                session.sendMessage(["apiKey": key], replyHandler: { reply in
                    DispatchQueue.main.async {
                        self.status = reply["saved"] as? Bool == true ? "手表已确认保存" : "手表保存失败，请解锁后重试"
                    }
                }, errorHandler: { _ in
                    DispatchQueue.main.async { self.status = "即时同步失败，配置仍在排队" }
                })
            }
        } catch { self.error = "配置同步失败，请解锁设备后重试。" }
    }

    private func receive(_ payload: [String: Any], completion: (([String: Any]) -> Void)? = nil) {
        #if os(watchOS)
        guard let key = payload["apiKey"] as? String else { completion?(["saved": false]); return }
        DispatchQueue.main.async {
            do {
                try Keychain.save(key)
                self.refresh()
                self.status = "已接收并保存 iPhone 配置"
                completion?(["saved": true])
            } catch {
                self.error = error.localizedDescription
                completion?(["saved": false])
            }
        }
        #else
        completion?(["saved": false])
        #endif
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        DispatchQueue.main.async {
            self.status = error == nil ? "连接已激活；\(session.isReachable ? "对端在线" : "对端暂不可达")" : "连接激活失败"
        }
        if !session.receivedApplicationContext.isEmpty { receive(session.receivedApplicationContext) }
    }
    func sessionReachabilityDidChange(_ session: WCSession) {
        DispatchQueue.main.async { self.status = session.isReachable ? "对端在线" : "对端暂不可达，可排队同步" }
    }
    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) { receive(applicationContext) }
    func session(_ session: WCSession, didReceiveMessage message: [String: Any], replyHandler: @escaping ([String: Any]) -> Void) {
        receive(message, completion: replyHandler)
    }
    #if os(iOS)
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) { session.activate() }
    #endif
}
