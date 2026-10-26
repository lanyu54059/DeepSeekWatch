# Windows 签名与 Apple Watch 安装

调研日期：2026-10-26。这里严格区分源项目报告、本应用构建证据与本应用实机测试。未接入你的 iPhone/Watch，以下实机步骤均尚未在你的设备验证。

## 已确认可行的范围

从 [社区项目说明](https://github.com/Rzbck/iloader-watch-companion) 可以确认：维护者报告过 Windows 驱动的 iPhone + 配对 Watch 安装并启动成功；这不是本应用的实机验证，也不代表上游正式版已支持。

该项目提供的回归版本为 Rzbck/iloader `70f37e9b4afc659ab44ec1944c034093f4cda416` 和 Rzbck/isideload `f7b9f3da570edd6824c29680545e710846d07df5`。它是社区入口文档仓库，实际代码在这两个 fork；不要把下载此文档仓库当作安装器。

上游 [nab138/iloader](https://github.com/nab138/iloader) 的 iPhone 侧载能力不能自动推导为 Watch 支持。选择发行物前核对其源代码提交与 Watch 功能说明。普通 AltStore、Sideloadly 也不能据此保证安装 Watch App。

## 本应用包结构：有条件可行

```text
Payload/DeepSeekPhone.app/
  Info.plist
  DeepSeekPhone
  Assets.car
  Watch/DeepSeekWatch.app/
    Info.plist
    DeepSeekWatch
    Assets.car
```

这与[社区测试文档](https://github.com/Rzbck/iloader-watch-companion/blob/main/docs/TESTING.md)的宿主加内嵌 Watch 形状相符。本应用是现代单目标 `WKApplication`，不需要独立扩展；不能因为没有 `.appex` 就判定损坏，也不能推断所有签名器都支持此结构。

CI 在打包前检查实际设备平台、Mach-O、编译资源和关联关系，并检查 ZIP 的 Payload。通过后仍需本机签名。编译、打包、签名、手机安装、手表安装和启动是六个不同阶段。

## 免费 Apple ID：有条件可行，具体覆盖尚未验证

本项目没有付费专用 entitlement；这减少配置需求，但不保证 Apple 免费账户能在第三方路径为两个目标签出有效 profile。需要为 iPhone 和配对 Watch 分别处理设备与 provisioning，嵌套 Watch 必须显式签名，最后签宿主。仅签主 App 不够。[社区架构说明](https://github.com/Rzbck/iloader-watch-companion/blob/main/docs/ARCHITECTURE.md)

需要保持：

| 字段 | 关联 |
| --- | --- |
| iOS CFBundleIdentifier | `com.personal.deepseek.phone` 或重签后的唯一标识 |
| Watch CFBundleIdentifier | 与宿主协调的 `.watchkitapp` 子标识 |
| Watch WKCompanionAppBundleIdentifier | 必须等于最终 iOS 标识 |
| application-identifier / TeamIdentifier / keychain-access-groups | 与各自证书和 profile 匹配，由签名工具处理 |

本工程无独立扩展；以后若增加扩展，其 `WKAppBundleIdentifier` 也必须指向最终 Watch 标识，并独立 provisioning/签名。不要把 iPhone profile 直接塞进 Watch bundle。

免费 Personal Team 通常按 7 天刷新开发 profile，并有 App ID/设备/安装数量限制；以本机实际签发的 profile 与 Apple 当前政策为准。[Apple 免费开发与会员说明](https://developer.apple.com/support/compare-memberships/) 不等于承诺 Windows 第三方签名支持。

## 安装操作：本应用尚未验证

1. 下载 Actions 成功运行的 artifact 并解压。确认 `validation.json` 为 `PACKAGED_UNSIGNED`，找到真实 `DeepSeekWatch-unsigned.ipa`。不把外层 artifact ZIP 当 IPA。
2. 记录 Windows、iOS、watchOS 版本，以及 iLoader/isideload 的具体提交。iPhone 和 Watch 应已正常配对，系统满足最低版本。
3. 从可信的项目发行页取得明确包含 Watch 支持的 Windows 构建。如仅提供源码或找不到能对应回归提交的发行物，停止安装阶段并按 fork 的构建说明构建工具；不要假设上游最新安装器包含这些实验改动。本说明未验证这些 fork 当前 Windows 发行包的供应与界面按钮名称。
4. 按所选版本说明安装其需要的 Apple USB 驱动/设备组件。USB 连接 iPhone、解锁、在手机上信任电脑。保持 Watch 已解锁并与手机连接。
5. 对开发签名应用，按系统提示在 iPhone 的“设置 → 隐私与安全性 → 开发者模式”启用并重启确认；Watch 如出现同类开发者模式要求，也按系统提示启用。不同系统开关可见性不同，不能保证 Windows 工具能触发初次开关。[Apple Developer Mode 说明](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device)
6. 在本机安装器登录自己的 Apple ID，完成它要求的验证。不要把密码、验证码、配对记录、私钥放进 GitHub 或 CI。选择此 IPA 和目标 iPhone，运行该版本的签名/安装流程。
7. 确认处理过程识别了 Watch bundle，并完成 Watch 设备 provisioning 与签名。如果只处理手机，说明这个工具/配置不满足要求。保留经过脱敏的第一处失败信息。
8. 确认手机 App 能打开。若系统要求，在手机“设置 → 通用 → VPN 与设备管理”信任对应开发者。随后确认 Watch App 实际安装；如手机 Watch App 提供该应用的安装入口，可尝试，但不能保证该入口能替代实验安装器的 companion 路径。
9. 等待手表安装完成并亲自打开，不能把占位图标当安装成功。打开两端 App，保存 Key、同步，在手表设置核对并发送一句测试问题。

没有经过设备测试的具体点击序列或命令均不冒充已验证教程。若工具需要 Mac 才能完成某一步，此 Windows 路径在该组合上即受阻，应记录而非跳过签名检查。

## 到期重新签名

在 profile 到期前，用同一 Apple ID 和同一标识映射对完整 IPA 重新签名并重装，包含 Watch。只刷新手机不保证手表能继续启动。换账号、重写不同标识或先卸载可能使系统视为新应用，密钥可能需要重填。聊天本来仅存当前进程，无云端恢复。此刷新流程尚未在本应用验证。

## 失败定位与兼容风险

按阶段检查：包结构 → 标识重写 → App ID/profile → 嵌套签名 → iPhone 安装 → Watch transport → Watch 安装 → Watch 启动 → API。iPhone 安装成功不能证明 Watch profile 合法。

Apple 系统升级可能改变配对与安装协议；社区记录没有覆盖所有系统、设备和 bundle 拓扑。[兼容性边界](https://github.com/Rzbck/iloader-watch-companion/blob/main/docs/COMPATIBILITY.md) 是判断依据，而不是跨版本保证。汇报问题只记录工具版本、系统版本、失败阶段和脱敏错误；不要公开 UDID、证书、profile、Apple 账户和配对资料。
