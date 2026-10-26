# iLoader Watch Apple ID 503 修复（Windows）

这是对 Rzbck 社区实验性 iLoader 的源码修补与 Windows CI 构建，**不是 Apple 官方工具**，未经设备实测与完整安全审计。

## 固定源码和补丁

- iLoader Watch 原始提交：70f37e9b4afc659ab44ec1944c034093f4cda416
- isideload Watch 原始提交：f7b9f3da570edd6824c29680545e710846d07df5
- 登录 503：移植 [nab138/isideload PR #11](https://github.com/nab138/isideload/pull/11) 的 X-Mme-Client-Info 改动，将 Xcode 客户端身份变为 com.apple.akd/1.0；上游作为 [iLoader 2.3.2](https://github.com/nab138/iloader/releases/tag/v2.3.2) 修复发布。
- Anisette：参考 [iLoader 2.3.9](https://github.com/nab138/iloader/releases/tag/v2.3.9)，默认使用 mac-ani.jkcoxson.com（第三方服务，不属于 Apple；旧配置可能需要手动修改）。
- Watch：Cargo 使用本地经过补丁的 **Rzbck/isideload** 源码，保留其 Watch 识别、签名及安装功能，不替换为无 Watch 补丁的普通上游。
- 安全：Keyring 不可用时拒绝登录，不允许退回文件存储；不禁用 TLS，也不绕开 Apple 双重验证；移除 Tauri devtools，停用容易覆盖 Watch 补丁的自动更新检查。

## 如何构建、下载

进入 [GitHub Actions 工作流](../../actions/workflows/iloader-watch-auth.yml)，运行 Build Watch iLoader with Apple login fix。仅在运行状态为绿色 success 并确实上传 Windows Artifact 时，从 iLoader-Watch-Auth503-Fixed-Windows 下载 ZIP，解压获得 iloader-watch-503-fixed-x64-setup.exe、exe-sha256.txt 和 patch-manifest.json。

CI 不会接触 Apple ID、密码、两步验证码、证书、私钥、设备配对数据或设备 UDID。产物可能没有 Authenticode 发布签名，不能因为编译成功就认为软件绝对安全。

## Windows 安装及实机验证

1. 校验 EXE 的 SHA-256，与构建产物中的值比较；使用经过更新的 Microsoft Defender 扫描。
2. 确保 Windows Credential Manager 可用；如果 iLoader 报 Keyring 错误，**停止登录**，不要禁用 Keyring。
3. USB 连接已解锁 iPhone，确认 Apple Watch 与它配对并解锁。
4. 建议使用专用 Apple Account，在 iLoader 完成官方 Apple 2FA，不勾选保存账号密码。
5. 检查 Settings 的 Anisette 服务，再通过 Import IPA 选择 DeepSeekWatch-unsigned.ipa，观察手机端与手表端的签名、部署和启动结果。

**注意：** Windows CI 编译成功并不证明已修复你设备上的全部 503、免费 Apple ID provisioning，也不证明你的 Watch 已成功安装。这三项必须分别实机验证。不要公开原始敏感日志。
