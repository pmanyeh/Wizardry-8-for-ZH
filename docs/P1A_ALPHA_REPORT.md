# P1A Alpha Transport Report

判定：**PASS**。計畫 v2.2；日期 2026-11-03（Asia/Taipei）。

## 實際驗證

- renderer / overlay / framebuffer readback：1920×1080。
- source：BGRA32，R/G/B/A 各 8 bits，straight alpha。
- 上傳：既有 stTexture2D 以 surface blit 取得 pixels；GPU `getTextureInfo` 回報 2048×2048 ARGB8888（內容區 1920×1080），tile count 1。
- shader：`0x0000c0b7`，SRC_ALPHA / ONE_MINUS_SRC_ALPHA，無 alpha test、無 depth write，nearest filtering。
- 輸出 framebuffer：BGRX32，RGB 各 8 bits；讀回經既有 surface API 正規化為 BGRA32 opaque。
- 沒有經過 JPEG、桌面截圖或尺寸縮放。

固定背景 RGB=(20,40,60)，相同前景 RGB=(220,180,80)。

| Source alpha | 預期 RGB | 實際 RGB | 絕對誤差 |
|---:|---|---|---|
| 0 | 20,40,60 | 20,40,60 | 0,0,0 |
| 64 | 70,75,65 | 70,75,65 | 0,0,0 |
| 128 | 120,110,70 | 120,110,70 | 0,0,0 |
| 192 | 171,145,75 | 171,145,75 | 0,0,0 |
| 255 | 220,180,80 | 220,180,80 | 0,0,0 |

公式：`round(background + (foreground-background)*alpha/255)`。另外逐一取樣 256 個 source alpha 值，最大 RGB 誤差 **0,0,0**，最終 RGB 有 241 組不同結果；RGB 輸出量化使部分相鄰 alpha 產生相同顏色，這不代表 alpha 遺失。

分析程式依 source texture / framebuffer 格式推導每 channel 4 的保守容許界線（alpha 量化、色彩量化、輸出及混合取整），實測沒有使用這個容許範圍。可就本次裝置、格式與路徑宣告 8-bit alpha transport preserved；不宣告其他 backend 已驗證。

## 重現

P0-A 與 P0-B 均先通過。主 repo baseline `7a0757a0ea9a0b03693a48a805485c892e07def0`，decomp baseline `ca63d4447a973815670fbf6e146110e5d46989f5`；本階段精確來源差異在 artifacts 的兩個 patch 中。retail EXE hash 仍為 `18A74FF61C65B8A2D4CFA11FFCE82AD7FEF022A94EAF0C2F217E479E981420D2`。

在 `C:\dev\wiz8-ws`（指向專案 local/wiz8-ws 的 junction）建置：

```powershell
. .\Tools\msvcenv.ps1
cmake --build build\vc2022 --target wiz8_sr_import_library
powershell -NoProfile -File scripts\hybrid\build_hybrid.ps1
```

在本專案根目錄啟動／要求讀回／分析：

```powershell
.\scripts\Start-PocRun.ps1 -Phase alpha
# 觀察並進入主選單後：
.\scripts\Request-PocCapture.ps1
python scripts\analyze_alpha_capture.py artifacts\p1a-alpha
```

Start-PocRun 將成對 Hybrid / hooks 安裝到 work 副本，並記錄 hashes 與 capture directory。遊戲只在收到 request 時從 renderer lockBuffer 讀取像素，不擷取桌面。

## 產物與限制

`artifacts/p1a-alpha/`：原始 source/readback BGRA、無損 PNG、完整 256 點誤差表、render-info、run-info、runtime/build logs 及 source patches。原版主選單及英文字仍可見，診斷區刻意覆蓋左上測試範圍。

首次連結遇到五個原版 SR.DLL 已提供、上游 consumer import library 尚未列入的 API；以實際 retail DLL export table 核對後補入 `imports/sr.def`。沒有改換 renderer 或 loader。

修改檔案：Video2.cpp（draw/readback/shutdown hooks）、Video2.h（既有 tile helper declaration）、sources.cmake、imports/sr.def、新增 zh_text/HiResTextLayer.h/.cpp，以及主 repo 的 transplant_wide.json（新增模組 compilation unit）。

中文字型／NPC layout：N/A — 留待 P1B／P2。此階段不宣稱中文字顯示或完整 UI 整合已通過。主選單證據可支持 UI 與呈現路徑仍運作；3D 場景相容性還會在 P1B 的短測試驗證。
