# P-1 架構採用報告

- 計畫：Master Plan v2.2；日期：2026-11-03（Asia/Taipei）。
- 判定：**PASS（原始碼層面的 P1 實作路線成立；不代表執行或渲染驗證通過）**。
- 執行範圍：P-1、P0-A、P0-B、P1A、P1B；不進入 P2A 或後續階段。

> 工作區搬移更新：依使用者後續指示，上游實體檔案移到本專案 `local/wiz8-ws`；`C:\dev\wiz8-ws` 保留為指向該目錄的相容 junction。基線 revisions 與既有證據不變。後續建置入口詳見 [WORKSPACE.md](WORKSPACE.md)。

## 固定基線

| 輸入 | 固定值 |
|---|---|
| 建置工作區 | `C:\dev\wiz8-ws` |
| 計畫及交付文件 | `D:\git\Wizardry 8 for zh` |
| 主 repository | `https://github.com/abr17/wiz8-widescreen.git` |
| 主 repository SHA | `7a0757a0ea9a0b03693a48a805485c892e07def0` |
| 主 revision 指定的 decomp SHA | `ca63d4447a973815670fbf6e146110e5d46989f5` |
| MinHook submodule SHA | `8af6b4acae5a9388fd742b56fa79ece89d96f823` |
| 本地功能分支（主 repo 及 decomp） | `zh-tw-hires-poc` |
| 唯讀遊戲來源 | `D:\SteamLibrary\steamapps\common\Wizardry8` |
| retail Wiz8.exe SHA-256 | `18A74FF61C65B8A2D4CFA11FFCE82AD7FEF022A94EAF0C2F217E479E981420D2` |
| 版本判定 | 與上游 GOG/Steam 1.2.4 支援 hash 一致 |
| 非 Git assets | 上游 `Wiz8Widescreen-1.0.2.zip`，僅匯入測試工作區 |
| assets 壓縮檔 SHA-256 | `819897F226DE9F5F53D2790FF400F89612D190EDA3E8D01CCB72C3ED429D55A1` |

`decomp` 使用的是主 repo 的 gitlink 指定 revision，不是任意獨立 HEAD。全部 Git 操作限本地，無 push。

## 參考專案與職責

| 專案 | 檢視時 HEAD | 用途 |
|---|---|---|
| `agluszak/wizardry-8-decomp` | `075cbd0b853c4670e94f6ae4fe48d53b52b5e819` | 原版文字、ABI 與 renderer 行為參考 |
| `agluszak/whizzardry-8` | `31a3dfd57ee99fec8ff4b47f4b9be449c42de2fa` | 現代化方向參考；本輪不移植或建置 |
| `munument1/Wizardry8-KR` | `9c27e019c50687806bf2bd0ca696fec22002fecb` | CJK 資源與 topic/save 問題參考；本輪不採用其二進位補丁 |

執行前已讀主 repo 的 `README.md`、`CLAUDE.md`、`docs/building.md`、`docs/hybrid.md`、`docs/testing.md`，以及 decomp 的 `AGENTS.md`、來源忠實度及 SurRender import visibility 文件。使用者已授權依 v2.2 做 runtime modernization；歷史重建規範中與此明確目標衝突的部分不作為另行要求核准的理由。建置輸入及遊戲副本留在上游指定工作區；本專案的計畫、報告與驗收證據交付到使用者工作區。

## P1 掛點

| 掛點 | 原版位址 | transplant 狀態 | 用途及座標 |
|---|---|---|---|
| `RenderFrame` | `0x00426790` | 已在 `transplant_wide.json` | 所有既有畫面層完成後、`endFrame()` 前呼叫診斷 overlay；輸入為 renderer physical pixels |
| `ShutdownVideoScenes` | `0x00423f30` | 已在清單（dependency） | 原 renderer 釋放前回收模組資源；無座標 |
| `InitializeRendererSceneObjects` | `0x00423500` | 已在清單 | 既有初始化參考；優先由首次有效 RenderFrame 延遲建立中文資源，不為新模組改動 retail layout |
| `stSurface2D` constructor | `0x0047dae0` | 已在清單（dependency） | 使用既有 surface/tiles；實際尺寸由 renderer 回報 |
| `stSurface2D::updateRectangle` | `0x0047e450` | 已在清單 | 明確更新 GPU texture；不能假設改 CPU buffer 就會自動上傳 |

P0-B 先只在 `RenderFrame` 加入一次性日誌標記，不加入任何 P1 功能。須證明新碼在 retail EXE + 本地建置 Hybrid 中執行，之後回復成對的乾淨 P0-A DLL/hooks。P1 才新增 `HiResTextLayer` 與 GDI rasterizer。

## 繪製路徑

1. 保留既有 `version.dll -> wiz8hy.dll -> HybridInstall`，不新增第二個 loader。
2. 模組明確持有 BGRA32 CPU buffer、`srColorSurface` 及 `stSurface2D`。P1 使用不掛入 transient UI scene 的獨立 node，由既有 RenderFrame 直接提交；避免 page retirement 將診斷層清除。
3. surface 寬高等於 `g_gerd->getWidth()/getHeight()`，正式 gate 必須為 1920×1080。
4. tile 大小先依既有 `SurfaceTileExtent` 能力判斷；不能超過 renderer 上限。surface 本身仍為精確 physical size。
5. 逐 tile 關閉 `HINT_NO_ALPHA` 與 `HINT_ONE_BIT_ALPHA`；不呼叫 `setAlphaTestEnabled()` 充當 smooth-alpha API。
6. 使用 straight alpha：RGB 不預乘，SRC_ALPHA / ONE_MINUS_SRC_ALPHA，alpha test/depth write 關閉，texturing/color write 開啟。
7. draw 前設定 full-output viewport/scissor 及正確矩陣，結束時恢復矩陣上下文；本輪診斷層刻意位於最上層，最後才 endFrame。
8. CPU pixels 變更後明確更新／invalidate tiles。用 `getTextureInfo()` 記錄實際 texture 格式，不能以 BGRA32 輸入直接推論裝置也保留 8-bit alpha。
9. `Enabled=0` 時不建立 surface/node/font，退出時明確釋放；保留原遊戲文字路徑。

來源依據：decomp `src/wiz8/engine_code/Video2.cpp` 的 `RenderFrame`、`RenderScene`、`SurfaceTileExtent`；`src/wiz8/surface2d.cpp` 的 constructor、`DrawTiles`、`updateRectangle`、alpha hint 開關；`include/surrender/srGERD.h` 的 format/readback API。上述是靜態證據，GPU 行為須由 P1A 驗證。

## 座標與 P2 遮擋方案

P1 diagnostic strings 直接指定 physical pixels，並附一組 logical-to-physical 定位證據。後續入口須先分類座標，不能把全部 X 值以 `/640` 轉換：

- game -> canvas：使用既有 draw origin / anchor；zone layout 則使用其 zone 映射，不能再重複加 origin。
- canvas -> physical：依 actual output / `g_canvas_w` 及 actual height / 480，含現有 viewport 語意。
- 從原繪製入口取得 command 時保存 source space、draw origin、anchor、zone、clip 及 owner/scope；context 改變須重建 command。

已定位現有 `CanvasDrawOrigin`、`CanvasAnchorShift`、`CanvasZoneMapX`、`CanvasZoneOverlayRect`。`CanvasCanvasToScreen` 是滑鼠 cell 對應工具，含取整與 MouseScale 行為，不能直接假定是文字邊界的精確變換。

P2 候選方案：在實際 UI 繪製入口保存被遮擋的範圍，將中文 command 的 clip 減去較上層 popup/modal 的 canvas rect，再按剩餘區域重播；screen/scope 隱藏時撤除 command。現有 `CanvasZoneOverlayRect` 只涵蓋啟用 zone layout 的情況，不能視為所有 NPC/modal 的通用遮擋登錄。P2 前仍須觀察指定 NPC 的 `DrawDialog`/modal 入口，驗證覆蓋資訊完整；不足時阻塞 P2，改研究與原 UI 交錯的繪製點。本輪只提交方案，不宣稱 P2 遮擋已通過。

## 證據與格式

上游 `SaveJpegScreenshot` 使用 JPEG，不能作像素驗收證據。P1 使用 `srGERD::lockBuffer()` 讀回，保存原始像素及格式，解鎖後離線轉無損 PNG。capture 是否為當前完成 frame，須以已知色塊及實際尺寸驗證，不假定 buffer 語意。

P1A：固定背景、五色塊、256 級 alpha ramp、預期/實際 RGB 與誤差、來源/上傳/texture/readback 格式。P1B：24/32/48 physical px 字、直接 raster output、原尺寸 screenshot 及 1:1 crop。GDI 從灰階 coverage 生成 alpha，不依賴 DIB 自動 alpha。

## 所有權與建置限制

- 沿用上游 MSVC 2022 x86、`/Zc:wchar_t-` 及既有 SR/CRT bridges，不更換 ABI。
- Hybrid 移除動態全域初始化；新 module 狀態使用零初始化 POD 與明確 Init/Shutdown，不依賴 STL 全域物件 constructor。
- 配置／釋放成對且由同一 owner 處理。新 module state 不加入 retail class layout。
- `.dll` 與 hooks 作為成對備份、安裝、回復產物；原始 Steam 安裝與 reference 不作測試啟動位置。
- 不修改或發布 retail EXE、DB、scripts 或 game assets；wide assets 僅供本地 baseline。未涉及對外散布授權結論。

## 判定與限制

P-1 PASS：已有現成 loader、具體 transplanted render hook、surface/alpha/texture/readback 路徑及隔離方式。P1 的 alpha、SR imports、texture 精度、readback timing 與實際 1080p 尚待執行證據；本報告不將靜態 API 支援當成 P1 通過。

本階段 build/install/launch：N/A — 架構調查；命令與產物記錄於後續 P0 報告。不執行 NPC、Item、Journal 翻譯。
