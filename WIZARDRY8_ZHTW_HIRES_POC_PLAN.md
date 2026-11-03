# Wizardry 8 繁體中文高解析文字 PoC 計畫

> 專案代號：Wizardry8-ZH-TW  
> 上游基礎：`agluszak/wizardry-8-decomp`  
> PoC 目標：在 **1920×1080** 實際輸出解析度下，保留原版 640×480 UI 佈局，但讓繁體中文字以實際 framebuffer 解析度產生與顯示。  
> 優先展示場景：**NPC 對話 → 物品/裝備說明 → Journal**。

---

## 0. 核心技術判斷

目前 upstream source 已足以支撐本 PoC。

已確認：

1. Wizardry 8 的 UI / 原生文字系統基本座標為 **640×480**。
2. `CHAR16` 實際為 Windows `wchar_t`，因此遊戲內部文字 API 已具備 16-bit wide character 基礎。
3. 原始 `gprintf/mprintf` 最終使用 bitmap font，將 glyph 畫入 640×480 / 16-bit UI buffer。
4. `Video2.cpp` 會將 640×480 UI 映射到實際 renderer 尺寸。
5. 遊戲已有 `stSurface2D`，可將任意尺寸的 `srColorSurface` 以 ortho texture layer 疊到畫面。
6. `srPixelConvert` 已支援 `BGRA32 / ARGB32 / RGBA32` 等含 alpha 的 32-bit surface。
7. `srShader` 已支援 `SRC_ALPHA / ONE_MINUS_SRC_ALPHA` blending。

因此 PoC 不應將中文字塞回原始 `.sti` bitmap font，而應建立一個獨立的 **High-Resolution CJK Overlay**。

---

# 1. PoC 成功定義

PoC 必須同時滿足以下條件，否則不得宣告成功。

## P1 — Renderer Proof

在 1920×1080 模式下，遊戲畫面最上層顯示：

`巫術 8｜繁體中文高解析文字測試`

要求：

- 字形不是 640×480 bitmap 放大。
- screenshot 放大檢視時，中文字邊緣明顯高於原始 UI font 的解析度。
- 背景透明。
- 不破壞 3D rendering。
- 不破壞原始英文字型。
- 不需要修改原始遊戲資源。

## P2 — NPC Dialog Proof

至少一段 NPC 對話以繁體中文顯示。

要求：

- 中文出現在原 NPC dialog text area。
- 可正常換行。
- 不超出 dialog clip rectangle。
- 英文原文可透過 debug switch 切回。
- 關閉對話後中文字不得殘留在畫面。

## P3 — Item Description Proof

至少一個物品：

- 中文名稱
- 中文說明

皆由高解析文字層顯示。

## P4 — Journal Proof

至少一段 Journal entry 以繁體中文顯示。

要求：

- 多行中文。
- 正常 scrolling。
- 中文換行不依賴英文空白。
- 捲動後不得出現殘影。

---

# 2. 非目標

PoC 階段不要做：

- 完整遊戲翻譯。
- 全部 UI 字串替換。
- Fan Patch 1.28 完整相容。
- 4K 最終最佳化。
- 全面 UI redesign。
- 原始 `.sti` 中文 bitmap font。
- 大規模資源格式重寫。
- 長時間 unattended / soak / burn-in test。
- 為了 binary matching 而維持 upstream 原版行為。

本分支是 **localization / modernization experiment**，不是 upstream faithful reconstruction branch。

---

# 3. Branch 策略

不要直接在 upstream reconstruction 的 canonical branch 上混入中文化功能。

建議：

```text
upstream/main
    │
    └── zh-tw-hires-poc
```

如果建立獨立 repository：

```text
Wizardry8-ZH-TW
```

請保留 upstream remote：

```bash
git remote add upstream https://github.com/agluszak/wizardry-8-decomp.git
```

所有中文化修改應集中在 feature layer，避免散落到 reconstructed historical code。

---

# 4. Baseline

## 4.1 固定 upstream revision

PoC 開始時記錄：

```text
UPSTREAM_COMMIT=<sha>
```

輸出：

```text
docs/poc-baseline.md
```

內容至少包含：

- upstream commit
- build environment
- GOG input version/hash
- renderer backend
- output resolution
- baseline screenshot
- baseline executable hash

## 4.2 Baseline build

遵循 upstream workflow：

```bash
uv sync --frozen
uv run wiz8 toolchain build vc6-sp5
uv run wiz8 prepare
uv run wiz8 build runtime
uv run wiz8 build SURRENDER
uv run wiz8 run
```

先確認 upstream unmodified runtime 可進入遊戲。

不要先改 code。

---

# 5. 1920×1080 Baseline

目前 upstream default runtime config 使用 800×600。

PoC 必須先確認 1920×1080 是否能由目前 renderer 正常建立。

新增一份 PoC runtime config，例如：

```text
config/runtime-zh-poc/3DVideo.CFG
```

不要直接覆蓋 canonical runtime config。

記錄：

```cpp
g_gerd->getWidth()
g_gerd->getHeight()
g_screen_width
g_screen_height
```

PoC 以 renderer 實際回報的：

```text
physical_width
physical_height
```

為高解析文字 surface 尺寸。

禁止假設一定是 1920×1080。

---

# 6. High-Resolution Text Overlay 架構

新增：

```text
include/wiz8/zh_text/
    HiResTextLayer.h
    HiResTextRasterizer.h
    HiResTextTypes.h

src/wiz8/zh_text/
    HiResTextLayer.cpp
    HiResTextRasterizerGDI.cpp
```

後續若導入 FreeType：

```text
    HiResTextRasterizerFreeType.cpp
```

## 6.1 HiResTextLayer

職責：

- 建立 physical-resolution transparent surface。
- 管理 `srColorSurface`。
- 管理 `stSurface2D`。
- 清空 overlay。
- 更新 dirty rectangle。
- 提供 logical → physical coordinate conversion。
- 管理 text draw command。
- 不處理翻譯資料。

建議介面：

```cpp
struct HiResTextRect
{
    int left;
    int top;
    int right;
    int bottom;
};

bool HiResTextInitialize();
void HiResTextShutdown();

void HiResTextBeginFrame();
void HiResTextEndFrame();

void HiResTextClear();

void HiResTextDraw(
    const wchar_t* text,
    int logical_x,
    int logical_y,
    const HiResTextRect* logical_clip,
    int font_role,
    unsigned long rgba);

int HiResTextMeasure(
    const wchar_t* text,
    int font_role);

bool HiResTextContainsCJK(
    const wchar_t* text);
```

---

# 7. Overlay Surface

建立一張：

```text
physical_width × physical_height × BGRA32
```

例如：

```text
1920 × 1080 × 4
```

約 7.9 MB，可接受。

使用：

```cpp
srColorSurface(
    srPixelConvert::SURFACE_BGRA32,
    pixels,
    physical_width,
    physical_height,
    physical_width * 4);
```

再建立：

```cpp
new stSurface2D(
    hi_res_surface,
    physical_width,
    physical_height,
    g_scene_overlay0,
    256);
```

第一版 tile size 建議：

```text
256
```

不要一開始使用大量小 tile。

---

# 8. Alpha Blend

原 `stSurface2D` 預設不是為 full 8-bit alpha text overlay 設計，因此 PoC 必須顯式設定：

- texturing = enable
- depth write = disable
- color write = enable
- pass = always
- source blend = source alpha
- destination blend = one minus source alpha

概念：

```text
SRC = SRC_ALPHA
DST = ONE_MINUS_SRC_ALPHA
```

同時：

- 移除 `HINT_NO_ALPHA`
- 使用含 alpha 的 surface format
- 不使用 one-bit alpha 作為最終方案

PoC 驗證項目：

```text
50% alpha glyph edge
```

必須能與原 UI 背景平滑 blend。

---

# 9. 第一版 Rasterizer：Win32 GDI

PoC 第一版 **先不要引入 FreeType runtime dependency**。

理由：

- upstream canonical toolchain 為 MSVC 6。
- Win32 GDI Unicode API 已可由 VC6 呼叫。
- `wchar_t` 已存在。
- CJK 不需要複雜 script shaping。
- 可快速證明「physical-resolution CJK overlay」是否成立。

## 9.1 Font

使用可合法散布的繁中字型，例如：

```text
Noto Sans CJK TC
Source Han Sans TC
```

注意：

**不要把字型 binary 直接 commit，除非其授權與散布方式已確認。**

Repo 可以只提供：

```text
fonts/README.md
```

以及本地：

```text
local/fonts/<font-file>
```

並加入 `.gitignore`。

若需要 private font：

```cpp
AddFontResourceExW(..., FR_PRIVATE, ...);
```

## 9.2 GDI rasterization

建立：

- 32-bit DIB
- memory DC
- `HFONT`
- Unicode `DrawTextW` / `TextOutW`

為了取得可靠 alpha：

1. 將 glyph 先畫成白字黑底。
2. 讀取 coverage。
3. 將 grayscale coverage 轉成 alpha。
4. 套用目標 RGB。
5. 寫入 BGRA overlay。

不要依賴 GDI 自動維護 DIB alpha channel。

---

# 10. 為什麼第一版不直接用 FreeType

FreeType 是正式版較好的方向，但 PoC 第一目標是：

> 證明 Wizardry 8 reconstructed renderer 可以顯示真正 physical-resolution CJK。

如果一開始加入 FreeType，會同時引入：

- modern compiler compatibility
- dependency build
- DLL ABI
- runtime deployment
- Wine loading
- font discovery

這些問題會污染核心驗證。

因此：

```text
P1/P2：GDI
P3/P4 後：抽象 rasterizer
Production：評估 FreeType
```

`HiResTextRasterizer` 必須從第一天就是 abstraction，禁止把 GDI 呼叫散落到 dialog code。

---

# 11. Logical → Physical Mapping

原 UI 邏輯：

```text
640 × 480
```

高解析 overlay：

```text
physical_width × physical_height
```

位置 mapping：

```cpp
px = logical_x * physical_width  / 640.0f;
py = logical_y * physical_height / 480.0f;
```

clip rectangle 同樣轉換。

## 字型尺寸

中文字型尺寸優先依 **垂直比例**：

```cpp
scale_y = physical_height / 480.0f;
physical_font_px = logical_font_height * scale_y;
```

不要將 glyph 本身依 16:9 非等比拉伸。

也就是：

- position 可以依 UI X/Y transform。
- glyph 保持正常 aspect ratio。
- line wrapping 使用 physical clip width。

這樣在 1920×1080 下，中文字仍保持正常字形比例。

---

# 12. P1：Hardcoded Renderer Proof

在任何 translation integration 前，先新增：

```cpp
HiResTextDebugDraw();
```

在 1920×1080 顯示：

```text
巫術 8
繁體中文高解析文字測試
Wizardry 8 ZH-TW
```

至少：

- 24px
- 32px
- 48px

三種 physical font size。

輸出：

```text
artifacts/p1-hires-overlay/
    screenshot-1920x1080.png
    render-info.txt
```

`render-info.txt`：

```text
renderer_width=
renderer_height=
overlay_width=
overlay_height=
surface_format=
font_name=
font_pixel_size=
```

## P1 STOP GATE

只有 P1 screenshot 明確證明：

```text
中文不是 640×480 raster 後再放大
```

才繼續。

若 P1 失敗：

停止。

不要進 NPC Dialog。

---

# 13. CJK Detection

第一版：

```cpp
bool HiResTextContainsCJK(const wchar_t* text)
```

至少辨識：

```text
U+3400–U+4DBF
U+4E00–U+9FFF
U+F900–U+FAFF
```

以及：

- 中文標點
- 全形標點

非 CJK text：

```text
走原始 gprintf/mprintf pipeline
```

CJK text：

```text
走 HiResTextLayer
```

PoC 不要一開始全面替換英文字型。

---

# 14. Text Metrics

只改 draw 而不改 metrics 會失敗。

目前 dialog layout 使用：

```cpp
StringPixLength()
GetFontHeight()
```

因此 CJK path 必須提供：

```cpp
HiResTextMeasure()
HiResTextGetLineHeight()
```

其結果要能轉回 logical units，供現有 layout 使用。

例如：

```cpp
logical_width =
    physical_width_of_text * 640.0f / renderer_width;
```

但 NPC 中文 paragraph 建議最終直接以：

```text
physical clip width
```

進行 CJK wrap，避免依英文 bitmap metrics。

---

# 15. 中文換行

英文原版主要依 word/space wrap。

繁中不可只依 whitespace。

PoC CJK wrap 規則：

允許一般漢字間換行，但至少避免：

### 不得出現在行首

```text
，。、！？：；）》】』」％
```

### 不得出現在行尾

```text
《【『「（
```

第一版不需要完整 UAX #14。

但禁止：

```text
split by space only
```

---

# 16. P2：NPC Dialog

第一個實際 integration target：

```text
src/wiz8/dialog_code/DialogTextEntry.cpp
src/wiz8/dialog_code/DialogTextArea.cpp
src/wiz8/dialog_code/NpcDialog.cpp
```

`W8DialogTextEntry::DrawLine()` 目前直接呼叫：

```cpp
gprintf(...)
```

PoC 可在此建立第一個 CJK routing point：

```cpp
if (HiResTextContainsCJK(line))
{
    HiResTextDraw(...);
}
else
{
    gprintf(...);
}
```

但必須同時處理：

- `StringPixLength`
- prefix color
- text color
- clip rectangle
- line height
- redraw / invalidate
- dialog close cleanup

---

# 17. Overlay Lifetime

High-res text 不能畫一次後永久留著。

推薦 PoC 模型：

## Retained Command List

不要只把文字直接畫到 overlay 後忘記來源。

建立：

```cpp
struct HiResTextCommand
{
    void* owner;
    wchar_t* text;
    HiResTextRect logical_bounds;
    int x;
    int y;
    int font_role;
    unsigned long rgba;
};
```

每個 UI owner：

```text
W8DialogTextEntry*
```

擁有一組 commands。

當 entry redraw：

```text
RemoveCommands(owner)
AddCommands(owner)
```

每 frame：

```text
clear high-res overlay
replay active commands
upload dirty/full overlay
```

PoC 初期可直接 full-surface clear/upload。

1920×1080 BGRA：

```text
~8 MB/frame
```

只為 PoC 可接受。

正式版再做 dirty rectangles / glyph atlas。

這比「猜測 InvalidateRegion 何時應清字」更可靠。

---

# 18. P2 Translation Source

不要先修改原始遊戲 data files。

PoC 建立外部 UTF-8 translation resource：

```text
poc/zh-tw/npc-dialog.json
```

例如：

```json
{
  "poc_npc_001":
    "歡迎來到多米納斯。這是一段用來驗證《巫術 8》高解析繁體中文顯示的測試文字。"
}
```

載入時：

```text
UTF-8 → UTF-16 wchar_t
```

禁止以 ANSI code page 作為繁中核心格式。

---

# 19. P3：Item / Equipment

P2 成功後再定位：

- item name
- item description
- equipment dialog

至少展示：

```text
名稱：烈焰長劍
傷害：……
說明：一把……
```

PoC 必須證明：

- 短文字
- 長文字
- 數字混排
- 英文 / 中文混排

皆正常。

---

# 20. P4：Journal

Journal 是長文與 scrolling 驗證。

至少建立一個 5～10 行繁中 entry。

驗證：

- CJK wrap
- scrolling
- clip
- redraw
- 頁面切換
- dialog close
- 無殘影

Journal 成功後，才可宣告：

```text
High-resolution Traditional Chinese text pipeline proven.
```

---

# 21. 驗證方式

避免長時間 burn-in。

每個 Phase 使用可重現、可截圖的短測試。

## P1

```text
啟動 → 主畫面 → screenshot
```

## P2

```text
載入固定 save → 開啟指定 NPC 對話 → screenshot
```

## P3

```text
載入固定 save → 開啟指定物品 → screenshot
```

## P4

```text
載入固定 save → Journal → scroll 固定距離 → screenshot
```

每階段保存：

```text
expected screenshot
actual screenshot
render metadata
commit SHA
```

---

# 22. 回歸規則

中文功能必須可關閉：

```text
WIZ8_ZHTW_HIRES_TEXT=0
```

或 config：

```ini
[ZH-TW]
Enabled=0
```

關閉時：

- 不建立 high-res overlay。
- 不載入中文字型。
- 不改 CJK metrics。
- 遊戲應盡量回到 upstream runtime behavior。

---

# 23. Source Isolation

中文化新增程式優先集中：

```text
src/wiz8/zh_text/
include/wiz8/zh_text/
poc/zh-tw/
docs/zh-tw/
```

既有 reconstructed code 僅允許加入薄薄的 integration hooks。

例如：

```cpp
if (HiResTextIsEnabled() && HiResTextContainsCJK(text))
    ...
else
    original_path();
```

避免把 localization logic 散進：

```text
Font.cpp
Video2.cpp
DialogTextEntry.cpp
NpcDialog.cpp
```

---

# 24. License Boundary

注意 upstream：

```text
src/sgp/
```

包含 Strategy First SFI Source Code License 的來源。

因此：

- PoC 優先避免大量修改 / 複製 SGP source。
- 新的 high-resolution localization layer 放在 `src/wiz8/zh_text/`。
- 若未來公開發布 fork，先重新確認 upstream 與 SGP license 的 redistribution 條件。
- 不將 GOG 原始遊戲資料 commit 到 repository。

---

# 25. Agent 第一階段工作指令

Agent 現在只執行：

```text
P0 + P1
```

不要自行進入 P2。

具體工作：

1. 建立 clean branch `zh-tw-hires-poc`。
2. 記錄 upstream SHA。
3. 完成 upstream baseline build/run。
4. 建立 1920×1080 test config。
5. 確認實際 renderer width/height。
6. 新增 `HiResTextLayer` 最小骨架。
7. 建立 physical-size BGRA32 surface。
8. 建立 `stSurface2D` overlay，parent 使用現有 overlay scene。
9. 設定 full alpha blending。
10. 使用 GDI rasterizer 畫硬編碼繁中字。
11. 顯示：
    - `巫術 8`
    - `繁體中文高解析文字測試`
    - `Wizardry 8 ZH-TW`
12. 擷取 1920×1080 screenshot。
13. 放大檢視中文字邊緣，證明不是 640×480 glyph upscale。
14. 產出：
    - `docs/P1_REPORT.md`
    - screenshot
    - modified-file list
    - exact run commands
    - known issues
15. 到此停止。

---

# 26. P1 驗收條件

以下全部 PASS 才能進 P2：

- [ ] upstream baseline 可執行
- [ ] renderer 實際輸出為 1920×1080，或明確記錄實際尺寸
- [ ] high-res overlay 可見
- [ ] 中文可正確顯示
- [ ] 中文背景透明
- [ ] glyph edge 有 anti-aliasing
- [ ] 原始 UI 未被高解析 overlay 取代
- [ ] 原始英文文字仍正常
- [ ] overlay 不影響 3D scene
- [ ] 關閉 ZH-TW feature 後可回到原路徑
- [ ] screenshot 與 P1 report 已產出

---

# 27. P1 失敗時禁止的行為

若 P1 失敗，不得：

- 先改成 `.sti` bitmap 中文。
- 先做大量中文翻譯。
- 先研究 NPC scripts。
- 先做 Item/Journal。
- 以「看起來應該可行」取代 screenshot。
- 長時間等待遊戲自動跑。
- 同時更換 renderer backend、字型系統和 translation format。

必須先定位：

```text
surface
alpha
scene order
coordinate transform
texture update
```

是哪一層失敗。

---

# 28. 預期最終架構

```text
Wizardry 8
    │
    ├── Original English / Bitmap Text
    │       └── SGP Font → 640×480 UI Surface
    │
    └── Traditional Chinese
            │
            ├── UTF-8 Translation Resource
            │       ↓
            ├── UTF-16 / wchar_t
            │       ↓
            ├── CJK Layout / Wrap
            │       ↓
            ├── HiResTextRasterizer
            │       ↓
            ├── BGRA32 Physical-Resolution Surface
            │       ↓
            └── stSurface2D / SurRender Alpha Overlay
                         ↓
                  Final Framebuffer
                  1920×1080+
```

---

# 29. PoC 之後

P1～P4 通過後才評估：

1. GDI → FreeType rasterizer。
2. Glyph atlas / cache。
3. Dirty rectangles。
4. 2560×1440 / 4K。
5. Fan Patch 1.28 compatibility。
6. 全遊戲 translation extraction。
7. NPC script / STRINGDATA / FACT 等資源 pipeline。
8. glossary / authority file。
9. automated screenshot regression。
10. release packaging。

---

# 30. 最重要原則

本 PoC 要證明的不是：

> Wizardry 8 能不能「塞進中文字」。

而是：

> Wizardry 8 是否能保留原版 UI 與遊戲 renderer，同時加入一個真正以實際顯示解析度 rasterize 的繁體中文文字層。

只要 P1 + P2 成功，整個繁中化專案的最大技術風險就已經被解除。
