# P1B High-Resolution Traditional Chinese Report

**P1B PASS；首輪 P-1 / P0-A / P0-B / P1A / P1B 全部 PASS。**

計畫：Master Plan v2.2。日期：2026-11-03（Asia/Taipei）。到此停止，未進入 P2A / NPC 翻譯。

## 實際結果

在 retail Wizardry 8 1.2.4 + 本地 Hybrid 上，以 GDI 在 physical pixels 直接 rasterize：

```text
巫術 8
繁體中文高解析文字測試
Wizardry 8 ZH-TW
```

三組 font em size：24、32、48 px，各含上述三行，共九個 runs。字型是本機安裝的 Microsoft JhengHei，`GetTextFaceW` 回報「微軟正黑體」；九個 runs 的 missing glyph 數均為 0。

原尺寸讀回：[主選單 1920×1080](../artifacts/p1b-hires-text/screenshot-1920x1080.png)、[3D 場景 1920×1080](../artifacts/p1b-hires-text/scene/screenshot-1920x1080.png)。

原始字形與裁切：[rasterizer output](../artifacts/p1b-hires-text/rasterizer-output.png)、[1:1 crop](../artifacts/p1b-hires-text/crop-1x.png)、[nearest 4× crop](../artifacts/p1b-hires-text/crop-nearest-upscaled.png)。放大圖僅供檢視，不作為唯一證據。

## 為何能證明沒有 640×480 中介放大

1. `HiResTextRasterize` 的 target 為 1920×1080 top-down DIB，CreateFontW 接收 -24 / -32 / -48 physical em sizes，沒有 logical-canvas raster 階段。
2. GDI calls 全部隔離在 `HiResTextRasterizerGDI.cpp`。DIB 先以白字／黑底產生灰階 coverage，檢查 RGB 三通道一致，再將 coverage 寫成 straight alpha；不採用 GDI DIB 的原始 alpha。
3. 該 physical-size BGRA32 buffer 直接交給 srColorSurface / stSurface2D。GPU texture query 回報 ARGB8888，2048×2048 texture 中承載 1920×1080 內容；nearest 1:1 sampling。
4. `readback.bgra` 直接由 renderer lockBuffer 取得，保存為無損 PNG；沒有桌面縮放、聊天縮圖或 JPEG。
5. 使用相同 Hybrid、相同 1920×1080 主選單、功能關閉時的獨立 readback 作為背景，逐像素計算：

```text
expected = round(original_background * (1-alpha) + rasterizer_rgb * alpha)
```

比較全部 **21,661 個非透明字形像素**，final framebuffer 與 expected 的最大 RGB 誤差為 **0,0,0**，超過預先設定 2 級誤差界線的像素數為 **0**。這同時驗證 source coverage、尺寸、定位與 final transport，超出「肉眼看起來比較清楚」的證據強度。

完整結果：[pixel-evidence.json](../artifacts/p1b-hires-text/pixel-evidence.json)。有 6,137 個 intermediate-alpha 像素，source coverage 共 16 個值；字形抗鋸齒存在。P1A 另以 256 級 ramp 驗證 8-bit alpha transport，不能把字形 coverage 的 16 個值誤認為 texture 只剩 4-bit alpha。

## 字型與座標

| physical font em | 三行頂端 y | 各行 cell height | 中文測試行寬 |
|---:|---|---:|---:|
| 24 px | 40 / 76 / 112 | 30 px | 264 px |
| 32 px | 174 / 218 / 262 | 40 px | 352 px |
| 48 px | 350 / 414 / 478 | 61 px | 528 px |

全部 x=48 physical pixels。九個 runs 都有有效 glyph 與 intermediate coverage，完整 ascent/descent/width/height 記於 render-info 與 pixel-evidence。

本輪刻意以 physical coordinates 定位診斷文字，保持字形比例。對一般 centered game coordinates，現有 canvas transform 是 `canvas_x = game_x + origin`，再以 renderer_width / g_canvas_w 與 renderer_height / 480 轉為輸出位置；anchor / zone context 必須依 P-1 的方案處理。P1 沒有接管實際 NPC logical layout，也不宣稱已驗證所有 logical-to-physical UI 情況。

## 開關與 3D 短測試

- Enabled=1：主選單原英文文字、寬 UI、游標仍正常；中文 overlay 背景透明。
- 載入原版 `Sample Party.SAV`，略過影片後進入 Lower Monastery 海灘。實際 3D 場景、水面、原版 HUD、游標與中文字共存；未修改任何遊戲資料，也未進行 NPC/Item/Journal 翻譯。
- 正常經 Options / Quit 結束測試，重新以相同 Hybrid + `Enabled=0` 啟動。
- Enabled=0：原主選單無中文字；metadata 回報 `overlay_width=0, overlay_height=0`，log 為 `disabled: no overlay resources`，未呼叫 GDI rasterizer 或建立中文字型。
- 功能關閉仍允許明確要求的診斷 readback；它不是 overlay 或中文字型資源。
- feature-off readback 在 `artifacts/p1b-feature-off/`。最後測試副本維持 Enabled=0。

## 原始碼、版本與重現

- 主 repo baseline：`7a0757a0ea9a0b03693a48a805485c892e07def0`。
- paired decomp baseline：`ca63d4447a973815670fbf6e146110e5d46989f5`。
- 本輪精確來源：`artifacts/p1b-hires-text/decomp.patch` 與 `hybrid-config.patch`，及專案 scripts；hash manifest 另附。
- retail EXE hash：`18A74FF61C65B8A2D4CFA11FFCE82AD7FEF022A94EAF0C2F217E479E981420D2`。
- Hybrid / hooks 的實際 build hashes 在 `run-info.json` 與 `hybrid-hashes.json`。binary 備份在 `local/wiz8-ws/build/zhtw/p1b`，未放入外層 Git。

由專案根目錄進入建置環境：

```powershell
. .\scripts\Enter-Upstream.ps1
. .\Tools\msvcenv.ps1
cmake --build build\vc2022 --target wiz8_sr_import_library
powershell -NoProfile -File scripts\hybrid\build_hybrid.ps1
```

由專案根目錄執行兩次獨立 run；每次都在主選單就緒後要求 readback，退出後再切換：

```powershell
.\scripts\Start-PocRun.ps1 -Phase text
.\scripts\Request-PocCapture.ps1
# 正常退出 text run 後：
.\scripts\Start-PocRun.ps1 -Phase off
.\scripts\Request-PocCapture.ps1
python scripts\analyze_text_capture.py artifacts\p1b-hires-text artifacts\p1b-feature-off
```

若追加 3D capture，先保留主選單的 readback/source/render-info，再保存 scene capture；現有 `menu/` 與 `scene/` 已分開。比較使用相同主選單背景，不能混用動態 3D 畫面作逐像素基準。

## 修改清單

decomp：

- `include/wiz8/engine_code/Video2.h`：既有 tile helper declaration。
- `src/wiz8/engine_code/Video2.cpp`：draw / readback / shutdown 三個薄掛點。
- `src/wiz8/imports/sr.def`：五個以 retail export table 驗證的新 consumer imports。
- `src/wiz8/sources.cmake`：分類兩個新增 compilation units。
- `include/wiz8/zh_text/HiResTextLayer.h`、`src/wiz8/zh_text/HiResTextLayer.cpp`。
- `include/wiz8/zh_text/HiResTextRasterizer.h`、`src/wiz8/zh_text/HiResTextRasterizerGDI.cpp`。

主 repo：`scripts/hybrid/transplant_wide.json` 新增兩個 module compilation units；既有 289 個 hooks 不變。P0-B 的一次性 marker 已移除。

## 已知限制與停止點

- 目前是固定文字、固定 1080p 的 renderer proof；沒有 Translation Resolver、CJK paragraph wrap 或實際 UI owner registry。
- 診斷文字刻意最上層，在 popup / loading / exit screens 也可見。P2 前必須另驗證真實 UI 遮擋與生命週期。
- 使用本機安裝字型，不散布字型 binary；其他機器的字型取得與 packaging 未完成。
- 未驗證 runtime resolution/device reset、其他 renderer、4K、Fan Patch 或其他 mods。
- 上游檔名測試的 CP950 fixture 限制詳見 P0 報告；本輪未修改該 subsystem。

首輪要求的證據已齊備。**停止，不進入 P2A 或 P2；下一步由使用者審閱原尺寸影像與報告。**
