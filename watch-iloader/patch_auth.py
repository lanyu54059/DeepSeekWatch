#!/usr/bin/env python3
"""Small, fail-closed forward-port of upstream auth fixes onto verified Watch forks.

No Apple account credentials, device records, or provisioning profiles are used
by this patcher or by its CI workflow.
"""
from __future__ import annotations
import argparse
import pathlib
import re

ROOT_ILOADER = "70f37e9b4afc659ab44ec1944c034093f4cda416"
ROOT_ISIDELOAD = "f7b9f3da570edd6824c29680545e710846d07df5"
DEFAULT_ANISETTE = "mac-ani.jkcoxson.com"

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected precisely one old-code anchor; found {count}. Refuse patch.")
    return source.replace(old, new, 1)

def edit(root: pathlib.Path, filename: str, function) -> None:
    path = root / filename
    before = path.read_text(encoding="utf-8")
    after = function(before)
    if after == before:
        raise ValueError(f"Patch did not change {path}")
    path.write_text(after, encoding="utf-8", newline="\n")
    print("PATCH", filename)

def patch_client(src: str) -> str:
    # Port the current upstream isideload RemoteV3AnisetteProvider technique:
    # /v3/client_info is served by the selected anisette server, not hardcoded
    # to the now-rejected 2026 Xcode identifier.
    old = '''        Ok(AnisetteClientInfo {
            client_info: "<Mac15,7> <macOS;27.0;26A5378j> <com.apple.AuthKit/1 (com.apple.dt.Xcode/25183.54.10)>".to_string(),
            user_agent: "akd/1.0 CFNetwork/808.1.4".to_string(),
        })'''
    new = '''        let info = self
            .client
            .get(format!("{}/v3/client_info", self.url))
            .send()
            .await
            .context("Failed to request /v3/client_info from anisette server")?
            .error_for_status()
            .context("anisette server returned an error for /v3/client_info")?
            .json::<AnisetteClientInfo>()
            .await
            .context("Failed to parse /v3/client_info response")?;
        if info.client_info.trim().is_empty() || info.user_agent.trim().is_empty() {
            return Err(report!("Anisette returned empty client information"));
        }
        Ok(info)'''
    return replace_once(src, old, new, "dynamic anisette client information")

def patch_grandslam(src: str) -> str:
    # Follow upstream's URL-bag header distinction so android-style client
    # information does not accidentally select the wrong GrandSlam endpoint.
    src = replace_once(
        src,
        'const URL_BAG: &str = "https://gsa.apple.com/grandslam/GsService2/lookup";',
        '''const URL_BAG: &str = "https://gsa.apple.com/grandslam/GsService2/lookup";
const URL_BAG_CLIENT_INFO: &str =
    "<Mac15,7> <macOS;27.0;26A5378j> <com.apple.AuthKit/1 (com.apple.akd/1.0)>";''',
        "grandslam URL bag constant",
    )
    src = replace_once(
        src,
        '''        base_headers: HeaderMap,
    ) -> Result<Dictionary, Report> {
        debug!("Fetching URL bag from GrandSlam");''',
        '''        mut base_headers: HeaderMap,
    ) -> Result<Dictionary, Report> {
        debug!("Fetching URL bag from GrandSlam");
        base_headers.insert(
            "X-Mme-Client-Info",
            HeaderValue::from_str(URL_BAG_CLIENT_INFO)?,
        );''',
        "grandslam URL bag client header",
    )
    return src

def patch_cargo(src: str) -> str:
    # Local path preserves the exact frozen Watch version + all its patches.
    old = 'isideload = { version = "0.3.17", features = ["fs-storage"], git = "https://github.com/Rzbck/isideload", package = "isideload", rev = "f7b9f3da570edd6824c29680545e710846d07df5" }'
    new = 'isideload = { version = "0.3.17", features = ["fs-storage"], path = "../../isideload/isideload", package = "isideload" }'
    return replace_once(src, old, new, "local patched isideload")

def patch_login_ui(src: str) -> str:
    return replace_once(src, '''    "anisetteServer",
    "ani.sidestore.io",''', '''    "anisetteServer",
    "mac-ani.jkcoxson.com",''', "login anisette default")

def patch_settings_ui(src: str) -> str:
    # Keep the setting key stable for existing installations; change the
    # fallback and list of choices, do not silently overwrite user selections.
    src = replace_once(src, '''    "anisetteServer",
    "ani.sidestore.io",''', '''    "anisetteServer",
    "mac-ani.jkcoxson.com",''', "settings anisette default")
    src = replace_once(src, '''let anisetteServers = [
''', '''let anisetteServers = [
  ["mac-ani.jkcoxson.com", "Jkcoxson (Mac, upstream v2.3.9 default)"],
  ["ani.jkcoxson.com", "Jkcoxson (Windows)"],
''', "settings anisette choices")
    return src

def patch_secure_storage(src: str) -> str:
    old = '''    } else {
        warn!(
            "Keyring is not available, falling back to filesystem storage for sideloading data. This is insecure!"
        );
        Ok(Box::new(FsStorage::new(
            app.path().app_data_dir().map_err(|e| {
                AppError::Filesystem("Failed to get app data directory: {:?}", e.to_string()))?
            })?,
        )))
    }'''
    # Use exact source-safe slice replacement: the original AppError has a
    # two-argument Filesystem variant, so accept only its verified contents.
    start = '    } else {\n        warn!(\n            "Keyring is not available, falling back to filesystem storage for sideloading data. This is insecure!"\n        );'
    if src.count(start) != 1:
        raise ValueError("keyring file fallback anchor missing")
    pos = src.index(start)
    tail = src[pos:]
    closing = '''        )))
    }'''
    # This method ends immediately after the fallback block.
    if tail.count("Ok(Box::new(FsStorage::new(") != 1 or closing not in tail:
        raise ValueError("keyring file fallback is not the expected code")
    old_block = tail[:tail.index(closing) + len(closing)]
    new = '''    } else {
        Err(AppError::Misc(
            "Secure credential storage unavailable. Refusing insecure filesystem fallback."
                .to_string(),
        ))
    }'''
    return src[:pos] + new + tail[len(old_block):]

def patch_disable_auto_updates(src: str) -> str:
    src = replace_once(src, 'import { checkForUpdates } from "./update";\n', "", "updater import")
    src = replace_once(src, '''  useEffect(() => {
    checkForUpdates();
  }, []);

''', '''  // Disabled in Watch experimental fork: official auto-updates would replace
  // the Watch-capable sideload implementation with an upstream-only release.

''', "updater call")
    return src

def patch_account(src: str) -> str:
    # fail fast, before any password or 2FA entry when Credential Manager is
    # unavailable; do not depend on the UI warning alone.
    needle = '''    let account = login(&handle, &window, &email, &password, anisette_server).await?;'''
    replacement = '''    if !crate::secure_storage::keyring_available() {
        return Err(AppError::Misc("Windows Credential Manager is unavailable; login refused".into()));
    }
    let account = login(&handle, &window, &email, &password, anisette_server).await?;'''
    if src.count(needle) != 2:
        raise ValueError(f"login secure storage guard: expected two login calls, found {src.count(needle)}")
    return src.replace(needle, replacement)

def patch_tauri_config(src: str) -> str:
    # The pinned fork enables Tauri updater bundles, which demand a *separate*
    # update-signing private key. We disabled auto-update above to preserve Watch
    # support; therefore no updater artifacts should be built or signed.
    return replace_once(
        src,
        '"createUpdaterArtifacts": true',
        '"createUpdaterArtifacts": false',
        "disable updater signing artifacts",
    )

def run(iloader: pathlib.Path, isideload: pathlib.Path) -> None:
    edit(isideload, "isideload/src/anisette/remote_v3/mod.rs", patch_client)
    edit(isideload, "isideload/src/auth/grandslam.rs", patch_grandslam)
    edit(iloader, "src-tauri/Cargo.toml", patch_cargo)
    edit(iloader, "src/AppleID.tsx", patch_login_ui)
    edit(iloader, "src/pages/Settings.tsx", patch_settings_ui)
    edit(iloader, "src-tauri/src/secure_storage.rs", patch_secure_storage)
    edit(iloader, "src-tauri/src/account.rs", patch_account)
    edit(iloader, "src/App.tsx", patch_disable_auto_updates)
    edit(iloader, "src-tauri/tauri.conf.json", patch_tauri_config)
    assert 'mac-ani.jkcoxson.com' in (iloader / 'src/AppleID.tsx').read_text()
    assert '/v3/client_info' in (isideload / 'isideload/src/anisette/remote_v3/mod.rs').read_text()
    print("PASS: nine pinned-source patch checks")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iloader", required=True, type=pathlib.Path)
    parser.add_argument("--isideload", required=True, type=pathlib.Path)
    args = parser.parse_args()
    run(args.iloader.resolve(), args.isideload.resolve())
