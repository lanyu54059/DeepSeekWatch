# Windows Apple Watch iLoader — Apple ID 登录兼容修补实验

这个目录实现了 Rzbck/iLoader Apple Watch 实验分支的**最小前移修复**：只将必要的认证变化和安全约束应用到两个经过 Watch 实机测试的特定 commit，而不是替换签名与 Watch 侧载主体。源码在 CI Runner 上下载、核对完整 commit SHA 并打补丁，不引入私有签名服务或 Apple 凭据。

- iLoader：`70f37e9b4afc659ab44ec1944c034093f4cda416`
- isideload：`f7b9f3da570edd6824c29680545e710846d07df5`
- Windows Actions：[watch-iloader-windows.yml](../.github/workflows/watch-iloader-windows.yml)
- 补丁源文件：[patch_auth.py](patch_auth.py)
- 背景：[上游 iLoader 2.3.2 修复 GSA 503](https://github.com/nab138/iloader/releases/tag/v2.3.2)、[上游 iLoader 2.3.9 修改默认 Anisette](https://github.com/nab138/iloader/releases/tag/v2.3.9)。

## 移植范围

1. 将旧的硬编码 Xcode AuthKit 客户端信息换成上游新版本使用的 `GET /v3/client_info`，失败时明确返回错误，而不是静默使用可能被 Apple 拒绝的旧标识。
2. 将认证 URL Bag 查询的 `X-Mme-Client-Info` 改成 upstream `com.apple.akd/1.0` 形式；仍然遵守正常 TLS 验证。
3. 将默认 Anisette 服务器调整为 `mac-ani.jkcoxson.com`，保留手动设置的功能，**不静默覆写已经保存的偏好**；也提供 `ani.jkcoxson.com` 切换选项。
4. 编译阶段将原有 Cargo `isideload` 依赖指向本地修补后的固定 commit，同时保留该 commit 的 Watch 配套签名实现。
5. 如果 Windows Keyring 不可用，拒绝 Apple ID 登录；移除向不加密文件系统回退的逻辑。
6. 禁用上游自动更新，否则升级到普通 iLoader 可能丢失 Watch 支持。

## 使用

1. 打开本分支的 [Windows Watch iLoader with Auth Fix 工作流](https://github.com/lanyu54059/DeepSeekWatch/actions/workflows/watch-iloader-windows.yml)，选择本分支并执行。构建成功后，下载对应 Artifacts，解压后得到 `iLoader-Watch-AuthFix-Windows-x64-setup.exe`、两份源码差异文件和 SHA-256。
2. Windows 上安装 Apple 官方 USB 设备驱动（iTunes/Apple Devices），用 USB 连接解锁的 iPhone，确保 Apple Watch 已配对。
3. 核对 EXE 哈希和文件来源，确认 Windows Credential Manager / Keyring 可用；系统警告不应凭空忽略。
4. 使用不存私人 iCloud 资料的专用 Apple Account，登录时**取消 Save Credentials**；双重验证码仅在本地程序输入。
5. 登录后选择 iPhone → **Import IPA** → 导入 DeepSeekWatch 的 **unsigned IPA**。
6. 检查 iPhone 与 Watch 是否真的都安装并启动。若出现签名、配对或手表传输错误，记录首条脱敏错误。**不要将 Apple 密码、2FA、配对文件、UDID、开发证书/私钥或 provisioning 文件提交到 GitHub。**

## 测试边界和风险

- 只有 CI 真正完成 Windows 编译并上传 EXE，才能称为已编译；Actions `success` 不等于 Apple 登录和设备安装已经通过。
- 这是非 Apple 官方软件，使用第三方 Anisette。源码透明不意味着经过审计；`mac-ani.jkcoxson.com` 是上游当前采用的第三方服务，不是 Apple 自有服务器。
- **CI 不登录 Apple、不会获得 Apple 账号密码，也不会签任何来自你的设备的 provisioning profile**。
- 禁止开发/危险调试模式；若 Keyring 报错，应停止，不要选择让其回退到文件系统。免费签名仍可能受 Apple 限制，有效期和设备数量按 Apple 当前政策。
- 该项目以保留 Watch 支持为优先。未来上游协议变化可能仍导致认证失败；修补不保证百分之百解决 503。

## 本地复现

在 Windows 电脑安装 Git、Python 3、Bun 和 Rust/Visual Studio Build Tools 后，从对应 SHA 分别检出 Rzbck 的两个仓库，在 `vendor/` 下分别放在 `iloader`、`isideload`，运行：

```powershell
python watch-iloader/patch_auth.py --iloader vendor/iloader --isideload vendor/isideload
cd vendor/iloader
bun install --frozen-lockfile
bun tauri build --bundles nsis
```

开发者可对比 Actions 上传的 `*-source-changes.diff` 复核所有改动。脚本仅在预期的确切代码锚点出现一次时修改，避免静默打到不兼容版本。