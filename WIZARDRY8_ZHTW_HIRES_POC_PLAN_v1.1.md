# Wizardry 8 繁體中文高解析文字 PoC 計畫 v1.1

> 專案代號：Wizardry8-ZH-TW  
> 上游基礎：`agluszak/wizardry-8-decomp`  
> PoC 目標：在 **1920×1080** 實際輸出解析度下，保留原版 640×480 UI 佈局，但讓繁體中文字以實際 framebuffer 解析度產生與顯示。  
> 優先展示場景：**NPC 對話 → 物品/裝備說明 → Journal**。  
> v1.1 修訂重點：固定 P0 建置環境、拆分 Alpha transport 與文字驗證、嚴格化 1920×1080 Gate、將 CJK 路由前移至 layout 前、補齊 retained-command lifetime/z-order，以及定義 PoC 字串來源識別策略。

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

## P1A — Alpha Transport Proof

先不要畫文字。

在 **1920×1080** physical-size BGRA32 overlay 上顯示固定測試色塊：

```text
Alpha 0
Alpha 64
Alpha 128
Alpha 192
Alpha 255
```

要求：

- `Alpha 0` 完全不可見。
- `Alpha 255` 完全不透明。
- 中間 alpha 必須與背景平滑混合。
- 不能退化成 one-bit alpha。
- 不影響 3D scene。
- 不改原始 640×480 UI surface。

P1A 未通過，不得進 P1B。

## P1B — High-Resolution Text Proof

在 **1920×1080** 模式下，遊戲畫面最上層顯示：

`巫術 8｜繁體中文高解析文字測試`

要求：

- glyph 必須直接 rasterize 到 physical-resolution surface。
- 禁止先畫到 640×480 再 upscale。
- 背景透明。
- glyph edge 有多階 alpha / anti-aliasing。
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


# 3. P0 建置環境與前置條件

本 PoC **不要先嘗試 Windows 原生建置流程**。

使用者主機可以是 Windows，但執行 upstream workflow 的基準環境固定為：

```text
Windows 11 host
    ↓
WSL2
    ↓
Linux distribution
    ↓
Docker / uv / Ghidra / Wine/GE-Proton workflow
```

建議基準：

```text
WSL2 + Ubuntu 24.04 LTS
Docker Desktop with WSL integration
Git
uv
Java 25
upstream pinned Ghidra fork
```

原因：

- upstream README 明確以 `uv`、Docker、Wine、Ghidra、CMake、reccmp 為主要開發流程。
- upstream 的 Ghidra 安裝步驟要求 Linux distribution。
- runnable build 使用 GE-Proton / umu runtime。
- PoC 第一階段的目標是驗證中文渲染，而不是同時建立另一套 Windows-native build system。

## 3.1 Windows 路徑規則

若 repository 位於：

```text
D:\git\Wizardry 8 for zh
```

Agent 必須記錄實際採用方式：

### Preferred

clone / checkout 到 WSL2 Linux filesystem，例如：

```text
~/src/Wizardry8-ZH-TW
```

不要把高 I/O build tree 放在 `/mnt/d/...`，除非已驗證效能與檔案語意沒有問題。

Windows 目錄可作為備份或成品輸出位置，但 canonical build checkout 優先位於 WSL filesystem。

## 3.2 Local configuration

依 upstream README 建立：

```bash
cp .env.example .env
cp config/local-inputs.example.yml config/local-inputs.yml
```

`.env` 至少確認：

```text
GHIDRA_INSTALL_DIR=
WIZ8_WORK_DIR=
遊戲輸入相關 absolute path
```

`config/local-inputs.yml` 至少確認：

```text
gog-media:
  <合法取得的 GOG Wizardry 8 installer 路徑>
```

不得將：

- GOG installer
- extracted retail game data
- local Ghidra project
- build products

commit 到 Git。

## 3.3 P0 Environment Report

Agent 必須產出：

```text
docs/P0_ENVIRONMENT.md
```

至少包含：

```text
Host OS
WSL distribution/version
kernel
Docker version
uv version
Java version
Ghidra revision
upstream commit SHA
WIZ8_WORK_DIR
game input variant
game input hash / installer hash
renderer backend
baseline output resolution
```

若 baseline 尚無法正常 build/run：

**P0 FAIL，停止。**

不得進 P1。

---

# 4. Branch 策略


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

# 5. Baseline

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

# 6. 1920×1080 Baseline

目前 upstream default runtime config 使用 800×600。

PoC 先做 renderer discovery，但 **正式 P1 Gate 固定要求 1920×1080**。

可分兩步：

### Resolution Discovery

允許先以 upstream 預設 800×600 確認：

- baseline 能啟動；
- renderer width/height 可讀取；
- PoC config 有被載入。

這一步只能標記：

```text
DISCOVERY PASS
```

**不能算 P1 PASS。**

### Formal P1 Resolution

正式 P1A / P1B 必須：

```text
renderer_width  = 1920
renderer_height = 1080
overlay_width   = 1920
overlay_height  = 1080
```

若目前 renderer/backend 無法建立 1920×1080：

```text
P1 BLOCKED
```

不得以 800×600、1024×768 或「已記錄實際尺寸」替代正式通過。

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

# 7. High-Resolution Text Overlay 架構

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

# 8. Overlay Surface

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

# 9. Alpha Transport：禁止直接依賴 setAlphaTestEnabled()

現有 `stSurface2D::setAlphaTestEnabled()` 的語意不適合平滑文字：

```text
false → HINT_NO_ALPHA
true  → HINT_ONE_BIT_ALPHA + alpha test
```

因此 High-Resolution CJK overlay **不得**把它當成 8-bit alpha 設定 API。

P1A 必須明確設定：

1. source surface 使用可表達 8-bit alpha 的格式，例如：

```text
SURFACE_BGRA32
```

2. 對 `stSurface2D` 每個 tile：

```text
disable HINT_NO_ALPHA
disable HINT_ONE_BIT_ALPHA
```

3. shader：

```text
texturing       = enable
depth write     = disable
color write     = enable
pass            = always
source blend    = SRC_ALPHA
destination     = ONE_MINUS_SRC_ALPHA
alpha test      = disable
```

4. texture upload 必須確認沒有在 conversion / upload 階段把 alpha 丟掉。

## 9.1 P1A Pixel Test

在 overlay 畫至少五個相同 RGB、不同 alpha 的方塊：

```text
A=0
A=64
A=128
A=192
A=255
```

保存：

```text
artifacts/p1a-alpha/
    alpha-test-1920x1080.png
    alpha-source-bgra.png
    alpha-pixels.txt
    render-info.txt
```

`alpha-pixels.txt` 至少記錄幾個已知背景位置與 composited output pixel。

禁止只以肉眼宣告 alpha 成功。

## 9.2 P1A STOP GATE

只有以下全部成立才進文字 rasterizer：

- transparent pixel 不可見；
- 25% / 50% / 75% alpha 有可區分的中間結果；
- opaque pixel 正常；
- 沒有 one-bit cutoff；
- 沒有整張 texture 被當 opaque；
- scene ordering 正確。

---

# 10. 第一版 Rasterizer：Win32 GDI

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

# 11. 為什麼第一版不直接用 FreeType

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

# 12. Logical → Physical Mapping

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

# 13. P1B：Hardcoded High-Resolution Text Proof

P1A 通過後，才新增：

```cpp
HiResTextDebugDraw();
```

在 **正式 1920×1080 renderer** 顯示：

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
artifacts/p1b-hires-text/
    screenshot-1920x1080.png
    rasterizer-output.png
    crop-1x.png
    crop-nearest-upscaled.png
    render-info.txt
```

要求：

- `screenshot-1920x1080.png` 必須是原始尺寸 PNG，不得經聊天軟體或網站縮圖再保存。
- `rasterizer-output.png` 必須保存 rasterizer 直接產生的 physical-resolution 文字輸出。
- `crop-1x.png` 保留中文字區域的 1:1 pixel crop。
- `crop-nearest-upscaled.png` 可放大 4×～8×供人工檢查，但不得作為唯一證據。

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

## P1B STOP GATE

只有以下全部成立才繼續：

```text
renderer      = 1920×1080
overlay       = 1920×1080
raster target = physical resolution
```

且原尺寸 PNG / rasterizer output / 1:1 crop 能共同證明：

```text
中文不是 640×480 raster 後再放大
```

才可標記：

```text
P1 PASS
```

若 P1 失敗：

停止。

不要進 NPC Dialog。

---

# 14. CJK Detection

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

# 15. Text Routing 與 Metrics

**CJK / high-resolution 路徑必須在 layout 之前決定。**

目前 `W8DialogTextEntry` 建構完成文字 buffer 後就會呼叫：

```cpp
UpdateLayout();
```

而現有 `W8TextBuffer::UpdateLayout()`：

- 以空白作為 break characters；
- 使用原始 `StringPixLength()`；
- 會在 buffer 中插入 `\n`。

因此：

> 不得等到 `DrawLine()` 才檢查 CJK。

## 15.1 Entry-level routing

對一個完整 paragraph / entry，先判斷：

```cpp
bool use_hires_text =
    HiResTextIsEnabled() &&
    HiResTextRequiresUnicodeLayout(full_entry_text);
```

只要 entry 進入 high-res path：

- 其中的繁中；
- ASCII 英文；
- 數字；
- 標點；
- NPC prefix；

必須使用同一套 metrics / wrap。

禁止一行中文裡讓 ASCII 使用 bitmap metrics、漢字使用 high-res metrics。

## 15.2 CJK-aware layout owner

PoC 可選：

```text
A. 擴充 W8TextBuffer，使 UpdateLayout 可委派 HiResText layout
B. 為 W8DialogTextEntry 建立 localization-specific layout path
```

但不得讓原始 `UpdateLayout()` 先改寫中文 buffer，再交給 high-res renderer。

## 15.3 Metrics API

目前 dialog layout 使用：

```cpp
StringPixLength()
GetFontHeight()
```

high-res path 必須提供：

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

# 16. 中文換行

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

# 17. P2：NPC Dialog

第一個實際 integration target：

```text
src/wiz8/dialog_code/DialogTextEntry.cpp
src/wiz8/dialog_code/DialogTextArea.cpp
src/wiz8/local_code/Controls.cpp
src/wiz8/dialog_code/NpcDialog.cpp
```

`W8DialogTextEntry::DrawLine()` 可以是**最終繪製掛點之一**，但不是 CJK 路由決策點。

路由必須在：

```text
full entry text
    ↓
choose layout path
    ↓
measure / wrap / line count
    ↓
draw
```

的第一步完成。

中文 entry 不得先經原始 whitespace-only `UpdateLayout()`。

必須同時處理：

- `StringPixLength`
- prefix color
- text color
- clip rectangle
- line height
- redraw / invalidate
- dialog close cleanup

---

# 18. Overlay Lifetime、Visibility 與 Z-order

High-res text 不能畫一次後永久留著。

PoC 採：

## Retained Command Registry

```cpp
typedef unsigned long HiResTextOwnerId;
typedef unsigned long HiResTextScopeId;

struct HiResTextCommand
{
    HiResTextOwnerId owner_id;
    HiResTextScopeId scope_id;

    wchar_t* owned_text;

    HiResTextRect logical_bounds;
    HiResTextRect logical_clip;

    int x;
    int y;
    int font_role;
    unsigned long rgba;

    int z_order;
    bool visible;
};
```

### 必要規則

1. `text` 必須由 command **持有自己的副本**。
2. 不得只保存外部 `wchar_t*`。
3. owner destructor / entry remove 必須呼叫：

```cpp
HiResTextRemoveOwner(owner_id);
```

4. panel/dialog/screen hide 必須呼叫：

```cpp
HiResTextSetScopeVisible(scope_id, false);
```

或移除該 scope。

5. scene change 必須清除不屬於新 scene 的 commands。
6. scrolling / relayout 必須更新 command 的 bounds / clip / position。
7. commands 必須具有穩定 z-order。

## 18.1 遮擋問題

不能假設：

```text
「每幀重播所有 commands」
```

就代表正確。

如果後來出現 modal dialog、popup、menu 蓋住 NPC dialog：

high-res text 也必須被相同 UI scope / z-order 規則遮住。

P2 至少測試：

```text
NPC dialog visible
→ popup/modal on top
→ popup close
→ NPC dialog restored
```

高解析文字不得浮在上層視窗之上。

## 18.2 PoC Replay

PoC 初期仍可每 frame：

```text
clear overlay
collect active visible commands
sort by z_order
replay commands
upload overlay
```

1920×1080 BGRA full refresh 只作 PoC 使用。

正式版再做：

```text
dirty rectangle
glyph atlas
partial upload
```

---

# 19. P2 Translation Source 與 Stable Text Key

不要先修改原始遊戲 data files。

但是也**禁止**使用沒有對應規則的任意 key，例如只有：

```text
poc_npc_001
```

卻不知道它如何穩定對應到遊戲 runtime 字串。

P2 先做一個小型：

```text
P2A — Source Identity Probe
```

## 19.1 P2A 目標

選定一個可重現 NPC 與一句可重現英文對話。

在文字進入 `W8DialogTextEntry` 前記錄可能的來源資訊，例如：

```text
NPC identifier
NPC script identifier
conversation/topic identifier
source string index / resource id
speaker
original text hash
call site / owner context
```

實際可取得哪些欄位，以 upstream source evidence 為準。

不得捏造不存在的 ID。

## 19.2 Stable Key 規則

優先順序：

```text
1. 遊戲本身穩定 resource/string ID
2. script + node/topic identity
3. NPC identity + source-local index
4. 最後手段：normalized original-text hash + context
```

若只能使用文字 hash：

- 必須同時保存 context；
- 必須在報告中標記它只是 PoC fallback；
- 不得宣稱已解決完整遊戲 stable ID。

## 19.3 Translation Resource

PoC translation resource：

```text
poc/zh-tw/npc-dialog.json
```

例如：

```json
{
  "npc:<npc-id>:topic:<topic-id>": {
    "source": "Welcome to Dominus.",
    "zh-TW": "歡迎來到多米納斯。"
  }
}
```

若真正可取得的 key 不是上述形式，使用 Agent 探測到的實際 stable identity。

核心文字格式：

```text
UTF-8 on disk
    ↓
UTF-16 / wchar_t in runtime
```

禁止以 ANSI code page 作為繁中核心格式。

## 19.4 P2A STOP GATE

必須先證明：

```text
同一個指定 NPC 對話
重啟遊戲 / reload save
→ 得到相同 translation key
```

才開始 P2 中文替換。

---

# 20. P3：Item / Equipment

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

# 21. P4：Journal

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

Journal 成功後，可宣告：

```text
High-resolution Traditional Chinese rendering and
the tested UI integration paths are proven.
```

**不得**因此宣告完整繁中化的主要風險全部解除。

仍未涵蓋的風險至少包括：

- 全遊戲資源抽取；
- stable string identity 覆蓋率；
- NPC script / resource translation pipeline；
- 其他 UI 類型；
- 字串長度與版面例外；
- 翻譯 authority/glossary；
- Fan Patch 相容性；
- release packaging。

---

# 22. 驗證方式

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

# 23. 回歸規則

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

# 24. Source Isolation

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

# 25. License Boundary

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

# 26. Agent 第一階段工作指令

Agent 現在只執行：

```text
P0 + P1A + P1B
```

不要自行進入 P2。

具體工作：

1. 在 WSL2/Linux canonical checkout 建立 `zh-tw-hires-poc`。
2. 記錄 upstream SHA。
3. 依 upstream README 完成 `.env` / `config/local-inputs.yml`。
4. 建立 `docs/P0_ENVIRONMENT.md`。
5. 完成 upstream baseline build/run。
6. 建立 1920×1080 PoC runtime config。
7. 確認 `g_gerd->getWidth()/getHeight()` 實際為 1920×1080。
8. 新增 `HiResTextLayer` 最小骨架。
9. 建立 1920×1080 BGRA32 surface。
10. 建立 `stSurface2D` overlay。
11. **不要呼叫 `setAlphaTestEnabled()` 當作平滑 alpha 解法。**
12. 明確設定 tile hints 與 alpha-blend shader。
13. 執行 P1A：0/64/128/192/255 alpha 色塊。
14. 保存 alpha source/output pixel evidence。
15. P1A PASS 後才建立 GDI rasterizer。
16. 顯示：
    - `巫術 8`
    - `繁體中文高解析文字測試`
    - `Wizardry 8 ZH-TW`
17. 擷取原尺寸 1920×1080 PNG。
18. 保存 rasterizer direct output 與 1:1 crop。
19. 證明 glyph 不是 640×480 upscale。
20. 驗證 ZH-TW feature off 時 overlay 完全不建立。
21. 產出：
    - `docs/P0_ENVIRONMENT.md`
    - `docs/P1A_ALPHA_REPORT.md`
    - `docs/P1B_HIRES_TEXT_REPORT.md`
    - screenshots / raster evidence
    - modified-file list
    - exact run commands
    - known issues
22. 到此停止。

---

# 27. P1 驗收條件

## P1A

- [ ] renderer = 1920×1080
- [ ] overlay surface = 1920×1080 BGRA32
- [ ] alpha 0 完全透明
- [ ] alpha 64 / 128 / 192 有可區分的 compositing
- [ ] alpha 255 正常不透明
- [ ] 沒有 one-bit cutoff
- [ ] alpha source/output evidence 已保存
- [ ] 原始 UI 與 3D scene 正常

## P1B

- [ ] 中文可正確顯示
- [ ] rasterizer target = physical resolution
- [ ] glyph edge 有 anti-aliasing
- [ ] 原尺寸 1920×1080 PNG 已保存
- [ ] rasterizer direct output 已保存
- [ ] 1:1 pixel crop 已保存
- [ ] 可證明不是 640×480 glyph upscale
- [ ] 原始英文文字仍正常
- [ ] 關閉 ZH-TW feature 後可回到原路徑
- [ ] P1A / P1B reports 已產出

只有以上全部 PASS：

```text
P1 PASS
```

才允許進 P2A。

---

# 28. P1 失敗時禁止的行為

若 P0 / P1A / P1B 任一失敗，不得：

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

# 29. 預期最終架構

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

# 30. PoC 之後

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

# 31. 最重要原則

本 PoC 要證明的不是：

> Wizardry 8 能不能「塞進中文字」。

而是：

> Wizardry 8 是否能保留原版 UI 與遊戲 renderer，同時加入一個真正以實際顯示解析度 rasterize 的繁體中文文字層。

P1 + P2 成功後，只能判定：

> 「physical-resolution 繁中文字顯示」與「NPC 對話整合」兩項核心技術風險已大幅降低。

完整繁中化仍必須另外驗證資源抽取、stable string identity、Item/Journal/其他 UI、翻譯資料管線與發行相容性。
