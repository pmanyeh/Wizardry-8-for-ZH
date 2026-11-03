# P0 環境與基線驗證

判定：**P0-A PASS；P0-B PASS；P0 PASS**。計畫：v2.2。日期：2026-11-03（Asia/Taipei）。

## 環境與輸入

- 實體 checkout：`D:\git\Wizardry 8 for zh\local\wiz8-ws`；建置入口：`C:\dev\wiz8-ws`（junction）。
- Windows 11 Pro：10.0.26300，build 26300。
- PowerShell：portable 7.6.9；上游 MSVC wrapper 使用系統 Windows PowerShell 5.1。
- MSVC 2022 portable：目錄 14.44.35207，compiler banner 19.44.35229 for x86；Windows SDK 10.0.26100.0。
- CMake：4.3.1-msvc1（複製自已安裝 Visual Studio 的工具目錄至本地 Tools）；未修改系統設定。
- llvm-mingw：20261020，clang 23.1.4，loader target i686。
- GPU：Intel Arc 140T；桌面 2880×1800；測試設定 window mode 1920×1080。
- 主 repo SHA：`7a0757a0ea9a0b03693a48a805485c892e07def0`。
- paired decomp SHA：`ca63d4447a973815670fbf6e146110e5d46989f5`。
- MinHook SHA：`8af6b4acae5a9388fd742b56fa79ece89d96f823`。
- 原始 Steam 來源：`D:\SteamLibrary\steamapps\common\Wizardry8`，未修改；`games/reference` 為唯讀副本，測試只在 `games/work`。
- retail EXE SHA-256：`18A74FF61C65B8A2D4CFA11FFCE82AD7FEF022A94EAF0C2F217E479E981420D2`。
- wide assets 由上游 1.0.2 release 匯入，zip hash：`819897F226DE9F5F53D2790FF400F89612D190EDA3E8D01CCB72C3ED429D55A1`。
- zlib 1.0.4 使用上游 build-inputs 所列 URL；SHA-256 `e5c260cd3db1370fb3e0c193e9cbd9f127a9bd055d622b3fb55b82747f6e5b24`。
- portable 工具／release 下載 hashes 見 `artifacts/p-1/download-results.json`。

## 建置、安裝與啟動

在建置入口執行：

```powershell
. .\Tools\env.ps1
.\build.ps1
powershell -NoProfile -File scripts\build\build-decomp.ps1
powershell -NoProfile -File scripts\hybrid\build_hybrid.ps1
Copy-Item build\version.dll,build\hybrid\wiz8hy.dll,build\hybrid\wiz8hy_hooks.txt games\work
Start-Process -FilePath games\work\Wiz8.exe -WorkingDirectory games\work
```

`wiz8wide.ini` 設定 `[Display] Mode=window, ScreenWidth=1920, ScreenHeight=1080`。遊戲改寫測試副本的 3DVideo.CFG 為 DirectX7 / 1920 / 1080 / 32；未修改來源安裝。

## P0-A

乾淨上游原始碼完成 loader、port import libraries 與 Hybrid 建置。Hybrid binding guard PASS，289 hooks。清單及完整建置紀錄、成對產物 hashes 在 `artifacts/p0-baseline/`；乾淨 binaries 留於 `build/zhtw/p0-baseline`。

實際啟動後 loader 確認 EXE hash、289 hooks loaded；canvas W=856、ox=108，renderer/window 1920×1080。已觀察片頭及主選單，英文 UI 正常。未加入中文程式碼。

### 基線截圖的限制

`baseline-native-1920x1080.jpg` 是未修改上游透過既有 `wiz8shot.req` 產生的原生尺寸 renderer JPEG。`baseline-1920x1080.png` 是該影像無縮放轉存，**仍繼承 JPEG 的損失，僅用於 P0 畫面與尺寸紀錄**。`baseline-window.jpg` 是 computer-use 的縮小視窗參考圖。兩者都不充當 P1 alpha／glyph 像素證據；P1 必須直接讀回像素並無損保存。

## P0-B 與回復

唯一修改是 `Video2.cpp::RenderFrame` 中的 13 行一次性日誌；未新增任何繪圖。`0x00426790` 原已在 transplant 清單。保存的 patch、probe build log 與 hashes 見 `artifacts/p0-transplant-probe/`。

實際安裝 probe DLL/hooks 並啟動，`execution-log.txt` 證明：

```text
[ZH-TW P0-B] RenderFrame active renderer=1920x1080
```

正常結束遊戲，從 `build/zhtw/p0-baseline` 成對回復 DLL/hooks 及 loader。三個檔案與乾淨備份逐一 hash 相同，見 `rollback-hashes.json`。重新啟動後主選單正常，`rollback-runtime.log` 不再有 probe marker，回復驗證 PASS。

中文顯示／resolver／中文字型：N/A — P0 尚未引入。

## 已知上游測試限制

額外執行現成 `test_filenames`：系統 code page 950 的部分有 10 個 failure；code page 1251、1252 及 Japanese 932 檢查通過。測試在系統 code page 下重用 cp1251 俄文字節 fixture，未對任意 Big5 環境保證可表示及不碰撞。這個結果不能當作繁中檔名支援通過。完整輸出保留於 `artifacts/p0-baseline/filename-tests.log`。

實際遊戲日誌顯示 code page 950、filename hook 沒有啟用。本輪使用 ASCII 遊戲路徑與原版 Sample Party save；未修改檔名 subsystem，未宣稱中文檔名／輸入支援。
