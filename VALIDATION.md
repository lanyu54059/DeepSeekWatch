# 构建与验证记录

日期：2026-10-26（台北时间）。

## 已确认：编译、测试、打包、下载

- [Actions run 40271590438](https://github.com/lanyu54059/DeepSeekWatch/actions/runs/40271590438)：`success`。
- 源码提交：`5a9e4b8ca59ee0b2cd6edd45bbf3e028de177665`。
- 环境：GitHub macos-26 ARM64 runner，Xcode 26.6 (17F113)，iPhoneOS / WatchOS SDK 26.5，XcodeGen 2.46.0。
- 原生 Swift API 测试成功：请求格式、多轮消息、中文响应、HTTP 401/402/403/429/400/5xx、解析失败、空回复、断网、超时、无 Key。测试使用 URLProtocol 模拟服务器，无真实密钥和 API 消费。
- Python 打包校验器 5 项测试通过，包括拒绝缺 Watch、错误关联、模拟器平台和假可执行文件。测试夹具不是发布产物。
- xcodebuild 输出 `BUILD SUCCEEDED`；目标图包含 DeepSeekPhone 和 DeepSeekWatch，执行嵌入与 ValidateEmbeddedBinary。
- [Artifact 12628087297](https://github.com/lanyu54059/DeepSeekWatch/actions/runs/40271590438/artifacts/12628087297) 已上传，并实际下载到 Windows、解压再次运行校验。
- IPA 大小：278386 字节。SHA-256：`4e0bb3c30b313c294608d3c2da06873281081f72900ad3d182215a8a0754c19d`。
- iOS 主 App：`Payload/DeepSeekPhone.app`，平台 iPhoneOS，最低 17.0。
- Watch App：`Payload/DeepSeekPhone.app/Watch/DeepSeekWatch.app`，平台 WatchOS，最低 10.0。
- Watch 的 `WKApplication = true`，`WKCompanionAppBundleIdentifier = com.personal.deepseek.phone`，可执行文件和 Assets.car 均存在。现代单目标结构，无独立扩展。
- 已回收 CI 生成的 `.xcodeproj` 到源码仓库，原始生成定义仍为 project.yml。

产物包含 unsigned IPA、真实 Products ZIP、生成工程 ZIP、工具链日志、编译日志、测试日志、打包日志和 validation.json。GitHub Artifact 依照工作流保留 14 天，到期需重跑构建。

## 尚未验证

免费 Apple ID 的各目标 profile 签发与重签、iPhone 安装/启动、Watch 安装/启动、真实配对设备的配置同步、真实 API 请求、听写输入、小屏实机布局及不同系统型号。没有已连接的 Apple 设备，不能据编译成功推断这些结果。

## 非阻塞日志提示

构建有“未使用 AppIntents，跳过元数据提取”和 iPad 界面方向提示；均未阻止原生目标编译与打包。工作流也记录第三方 action 的 Node 运行时弃用提示。完整日志随产物提供。

## 2026-10-26：第二次构建的独立产物验证

- [Actions #2（run 40271896706）](https://github.com/lanyu54059/DeepSeekWatch/actions/runs/40271896706)：编译、单元测试、结构校验、打包和产物上传全部成功。
- [Artifact 12628638465](https://github.com/lanyu54059/DeepSeekWatch/actions/runs/40271896706/artifacts/12628638465) 已实际下载并再次解压检查；Artifact ZIP 的 SHA-256 为 `af1e440005b54ecf327236813e5a24da1da055f619a6cb1e27c4c8698b607a0a`。
- 内部真实 unsigned IPA 为 278386 字节，SHA-256 为 `55704a432fb32ced259a44d9214aaae492f36c295fe06e8f938d925cc5b51ab6`，ZIP CRC 检查通过，共 14 个条目。
- 已实际检查 Payload/DeepSeekPhone.app/DeepSeekPhone 与 Watch/DeepSeekWatch.app/DeepSeekWatch 均包含非空 Mach-O 可执行文件及 Assets.car；两应用分别为 iPhoneOS、WatchOS 平台，最低系统为 iOS 17.0 / watchOS 10.0。
- 标识符为 `com.personal.deepseek.phone`、`com.personal.deepseek.phone.watchkitapp`，Watch 的 `WKCompanionAppBundleIdentifier` 正确指向前者，`WKApplication = true`。采用现代单 Target Watch App，没有独立 .appex。
- 验证范围止于无签名打包，**不能证明免费 Apple ID 签名或 Windows → iPhone → Apple Watch 实机安装成功**。
