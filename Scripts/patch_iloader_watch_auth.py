#!/usr/bin/env python3
"""Strict patch of pinned Rzbck Watch builds; no credentials in CI."""
import argparse
import json
from pathlib import Path
A="70f37e9b4afc659ab44ec1944c034093f4cda416"
B="f7b9f3da570edd6824c29680545e710846d07df5"
def change(root,file,old,new,n=1):
    f=root/file
    text=f.read_text(encoding="utf-8")
    if text.count(old)!=n: raise RuntimeError(f"{file}: source mismatch; expected {n}, got {text.count(old)}")
    f.write_text(text.replace(old,new),encoding="utf-8")
def run(a,b,manifest):
    a,b=Path(a),Path(b)
    change(b,"isideload/src/anisette/remote_v3/mod.rs",
       "<Mac15,7> <macOS;27.0;26A5378j> <com.apple.AuthKit/1 (com.apple.dt.Xcode/25183.54.10)>",
       "<Mac15,7> <macOS;27.0;26A5378j> <com.apple.AuthKit/1 (com.apple.akd/1.0)>")
    change(a,"src-tauri/Cargo.toml",
       f'git = "https://github.com/Rzbck/isideload", package = "isideload", rev = "{B}"',
       'path = "../../isideload/isideload", package = "isideload"')
    change(a,"src-tauri/src/secure_storage.rs",
       "fs_storage::FsStorage, keyring_storage::KeyringStorage, storage::SideloadingStorage",
       "keyring_storage::KeyringStorage, storage::SideloadingStorage")
    change(a,"src-tauri/src/secure_storage.rs",
       """        warn!(
            "Keyring is not available, falling back to filesystem storage for sideloading data. This is insecure!"
        );
        Ok(Box::new(FsStorage::new(
            app.path().app_data_dir().map_err(|e| {
                AppError::Misc(format!("Failed to get app data directory: {:?}", e))
            })?,
        )))""",
       '        Err(AppError::Keyring("Secure OS keyring unavailable; refusing unsafe filesystem storage.".into()))')
    change(a,"src-tauri/src/secure_storage.rs","use tauri::{AppHandle, Manager};","use tauri::AppHandle;")
    for file,n in [("src/AppleID.tsx",1),("src/pages/Settings.tsx",2),
                   ("src/ErrorContext.tsx",1),("src/components/OperationView.tsx",1)]:
        change(a,file,'"ani.sidestore.io"','"mac-ani.jkcoxson.com"',n)
    change(a,"src/pages/Settings.tsx","let anisetteServers = [\n",
       'let anisetteServers = [\n  ["mac-ani.jkcoxson.com", "Jkcoxson (Mac)"],\n  ["ani.jkcoxson.com", "Jkcoxson (Windows)"],\n')
    change(a,"src/App.tsx",'import { checkForUpdates } from "./update";\n',"")
    change(a,"src/App.tsx","  useEffect(() => {\n    checkForUpdates();\n  }, []);\n","")
    change(a,"src-tauri/Cargo.toml",'tauri = { version = "2", features = ["devtools"] }',
           'tauri = { version = "2", features = [] }')
    assert (b/"isideload/src/sideload/sideloader.rs").exists()
    assert "FsStorage" not in (a/"src-tauri/src/secure_storage.rs").read_text()
    assert "com.apple.akd/1.0" in (b/"isideload/src/anisette/remote_v3/mod.rs").read_text()
    assert 'path = "../../isideload/isideload"' in (a/"src-tauri/Cargo.toml").read_text()
    manifest=Path(manifest);manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps({"source_iloader":A,"source_isideload":B,
       "status":"SOURCE_PATCHED_LOGIN_NOT_TESTED","keep_watch_support":True,
       "secure_keyring_required":True,"auto_update_disabled":True,
       "github_actions_receives_apple_credentials":False},indent=2),encoding="utf-8")
    print("PASS: patched Watch-enabled source and auth without credentials")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--iloader",required=True)
    p.add_argument("--isideload",required=True)
    p.add_argument("--manifest",required=True)
    s=p.parse_args()
    run(s.iloader,s.isideload,s.manifest)
