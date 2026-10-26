# DeepSeek Watch

原生 SwiftUI 私人聊天应用。手表直接使用 URLSession 访问 DeepSeek，iPhone 提供安装容器和配置同步。无需自建服务器、第三方 HTTP 库或付费开发者能力。

## 验证状态

已在 [GitHub Actions 首轮构建](https://github.com/lanyu54059/DeepSeekWatch/actions/runs/40271590438) 成功通过 Xcode 26.6 的 iOS + watchOS 编译、API 合约测试、5 项打包校验器测试及真实 IPA 结构验证，并下载产物在 Windows 再次核对。详见 [验证记录](VALIDATION.md)。免费 Apple ID 签名、iPhone 安装、Watch 安装、实机 API 请求均未验证；CI 成功不代表这些阶段成功。

## 功能

- 黑色背景、圆角气泡、中文、多段回答和系统滚动；系统 TextField 提供设备支持的键盘/听写输入。
- 多轮聊天：保留当前进程会话，发送最近 6 轮和当前问题。退出进程不保留记录。
- 异步请求、加载状态、重复发送保护、失败重试（不重复添加问题）、清空会话并取消请求。
- 中文错误：未配置密钥、401/402/403/429/5xx、超时、断网、JSON 错误与空回复。
- 默认 `deepseek-flash`，设置可选 `deepseek-v4-pro`。非流式、4096 输出 token 上限，关闭 thinking 以减少等待。默认简答，可明确要求详细回答。
- iPhone 与手表分别使用设备 Keychain。WatchConnectivity 仅同步配置。在线同步带保存确认，离线同步排队，排队不代表已保存。
- 两个设备均可清除本机密钥；需分别清除。离线排队的旧同步仍可能在接收时写入，因此彻底停用旧 Key 时应同时清除两端并在 DeepSeek 控制台撤销该 Key。

## 目录

```text
DeepSeekPhone/    iOS 设置和安装容器
DeepSeekWatch/    watchOS 聊天、请求与状态
Shared/           Keychain、WatchConnectivity
Scripts/          工程生成、图标生成、真实产物校验和 IPA 打包
Tests/            API 合约测试、打包校验器测试
project.yml       完整 XcodeGen 工程定义
.github/workflows/build.yml
INSTALL_WINDOWS.md
```

采用现代单目标 Watch App：可执行文件在 Watch `.app` 内，无单独 WatchKit `.appex`。iOS 通过目标依赖内嵌 Watch App。仓库附有首轮 macOS 构建生成的完整 `.xcodeproj` 和基础图标；CI 按 project.yml 重新生成并上传工程，不需要 Windows 上运行 Xcode。

## 仅使用 Windows 构建

1. 本项目仓库为 [lanyu54059/DeepSeekWatch](https://github.com/lanyu54059/DeepSeekWatch)。自己新建仓库时，在 GitHub 点击 New repository，上传本目录全部文件，注意包含隐藏目录 `.github`。也可用 Git 推送；不要上传密钥和签名资料。
2. 在仓库 Actions 中启用工作流。push 自动构建；也可打开 Build DeepSeek Watch → Run workflow → main。
3. 工作流使用 `macos-26`，记录 Xcode/SDK，安装 XcodeGen，生成图标和工程，测试 API 合约，再用 `CODE_SIGNING_ALLOWED=NO` 构建真实 iPhoneOS/WatchOS Release 产品。
4. 成功后打开运行页面底部 Artifacts，下载 `DeepSeekWatch-unsigned-运行序号`，解压外层 GitHub artifact ZIP。
5. 内含 `DeepSeekWatch-unsigned.ipa`、`DeepSeekWatch-build.zip`、`DeepSeekWatch-xcodeproj.zip`、日志和 `validation.json`。IPA 是包含真实 Mach-O 可执行文件的 ZIP，尚未签名，不能直接安装。
6. 按 [Windows 安装说明](INSTALL_WINDOWS.md) 在本机尝试签名和安装。无需 Actions secrets，也不要上传 API Key 或 Apple ID 密码。

构建失败时工作流仍上传日志；如已有编译产品，保留 `DeepSeekWatch-failed-products.zip`。只有完整校验通过才生成正常 IPA。产物默认保留 14 天，请及时下载。Runner、Homebrew 与工具更新可能影响可重复性，实际版本见日志。

## API Key 配置

安装并启动 iPhone App，在 SecureField 输入 Key → 保存 → 同步到 Apple Watch。先打开手表 App 并解锁两端。显示“手表已确认保存”才代表即时同步成功；排队状态请到手表设置核对“已配置”。手表端也可直接手动输入保存作为备用方案。

手表首页输入问题并发送。发生错误后先修复网络/配置，再点重试；或清空后重新提问。长回答可用数码表冠滚动。同步不转发聊天，联网由系统处理，手表通过配对手机网络或自身 Wi-Fi/蜂窝网络请求 API；后台挂起可能中断请求，建议保持应用前台。

## 兼容性

最低 iOS 17 / watchOS 10。Series 4 及更新型号是否能用，仍取决于实际系统和配对要求；Series 0–3 无法升级到 watchOS 10，因此不支持。本项目并未逐一验证型号。新系统的开发签名、配对协议及 Windows 工具支持可能不同。系统听写取决于语言、地区及设备配置。

固定标识：`com.personal.deepseek.phone` 与 `com.personal.deepseek.phone.watchkitapp`。如改前者，必须同时改后者前缀和 `WKCompanionAppBundleIdentifier`，以及 Scripts/package.py 中对应校验。签名工具重写标识时也必须保持这一关系。

## 故障排查

| 现象 | 操作 |
| --- | --- |
| CI 失败 | 下载日志，找最早的 error；确认 macOS Runner 与 watchOS SDK 可用 |
| 打包失败 | 看 package.log；不要忽略 Watch 缺失或用模拟器 `.app` 代替 |
| iPhone 安装成功，手表没有 | 检查工具是否包含实验性 Watch 支持，查看 Watch provisioning、签名和 companion transport 阶段 |
| 同步一直排队 | 打开两端 App、解锁、检查配对与 Watch App 是否已装；重新点同步 |
| 钥匙串失败 | 解锁设备后重试；不同签名身份可能导致旧 Key 不可访问，重新配置 |
| 401 / 402 / 429 | 分别检查 Key、余额、调用频率；不自动循环重试 |
| 超时/断网 | 检查配对手机和手表网络，保持前台后手动重试 |
| 免费签名过期 | 重新签名完整 IPA，并重新安装两端；详见安装文档 |

## 安全与限制

密钥不进入源代码、Info.plist、UserDefaults 或日志。Keychain 使用本机且仅解锁可访问的保护级别。配置通过 Apple WatchConnectivity 传输；聊天和必要上下文发往 DeepSeek 官方 HTTPS API，按其账户计费与数据政策处理。会话仅在内存，但请求内容仍会离开设备。

不使用 App Groups、iCloud、推送、HealthKit、共享钥匙串等额外能力。没有 App Store/TestFlight 发布配置。免费账户和第三方工具的支持边界参见安装文档，不能保证每个系统组合都能安装。

## 参考

- [DeepSeek Chat Completions 官方格式](https://api-docs.deepseek.com/api/create-chat-completion/)
- [Apple Watch 工程设置](https://developer.apple.com/documentation/watchOS-Apps/setting-up-a-watchos-project)
- [XcodeGen 工程定义](https://github.com/yonaskolb/XcodeGen/blob/master/Docs/ProjectSpec.md)
- [实验性 Watch 安装路径](https://github.com/Rzbck/iloader-watch-companion)
