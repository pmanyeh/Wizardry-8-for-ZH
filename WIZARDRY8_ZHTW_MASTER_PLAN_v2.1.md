# Wizardry 8 Traditional Chinese Runtime Localization Mod
## Master Plan v2.1

**Project:** `Wizardry8-ZH-TW`  
**Plan version:** 2.1  
**Date:** 2026-11-03  
**Primary target:** Windows / Wizardry 8 GOG/Steam 1.2.4  
**Primary strategy:** Non-destructive Runtime Localization Mod  
**Primary PoC base:** `abr17/wiz8-widescreen` + `abr17/wizardry-8-decomp:widescreen`  
**Behavior/source oracle:** `agluszak/wizardry-8-decomp`  
**Long-term engine reference:** `agluszak/whizzardry-8`  
**CJK localization oracle:** `munument1/Wizardry8-KR`

---

# 0. Executive Summary

This project is **not** intended to create a permanently modified “Chinese edition” of Wizardry 8.

The target is a **Traditional Chinese localization mod** that is:

- runtime-based where practical;
- non-destructive toward game/content data;
- true high-resolution;
- Unicode/CJK capable;
- disable-able and removable;
- conservative toward unknown or modded content;
- designed so installing Traditional Chinese support does not unnecessarily block other Wizardry 8 mods.

The project does **not** currently aim to translate third-party mods.

Required behavior:

```text
Known vanilla text
    -> Traditional Chinese

Unknown mod-added text
    -> original text

Vanilla text modified by a mod
    -> original mod text

Localization disabled
    -> original game behavior
```

Core philosophy:

> **Presentation override, not content ownership.**

Wizardry8-ZH-TW should own presentation of known vanilla text, not replace or take ownership of gameplay mods, databases, scripts, or other content unless a narrow adapter absolutely requires it.

---


## 0.1 v2.1 Revision Focus

v2.1 incorporates the first Agent architecture review and strengthens seven areas:

1. atomic Hybrid baseline pairing and transplant proof;
2. explicit coordinate-space and modal-occlusion planning;
3. quantitative alpha transport evidence;
4. transactional original-text fallback;
5. resolver encoding/fingerprint/ownership contracts;
6. NPC/item/journal interaction and save invariance;
7. separation of Technical Preview readiness from localization Release Candidate readiness.

These are acceptance-contract changes, not a change to the core v2.0 product direction.


# 1. Final Architecture Decision

## 1.1 `agluszak/wizardry-8-decomp`

Role:

- source/behavior authority;
- text and layout flow oracle;
- resource-identity research source;
- NPC/dialog/item/journal implementation reference;
- reference for original 640x480 assumptions.

Do not use it as the first shipping architecture unless later evidence requires it.

## 1.2 `abr17/wiz8-widescreen`

Role:

- **primary short-term PoC base**;
- practical Windows/MSVC 2022 build workflow;
- Hybrid replacement on top of the original retail executable;
- widescreen coordinate/canvas implementation;
- existing UI/layout/render hook oracle;
- practical release/install model for retail 1.2.4.

Do not reimplement work it already solved:

- Windows-native build;
- Hybrid injection;
- wide canvas;
- aspect-aware mapping;
- UI/mouse coordinate conversion;
- existing function transplantation.

Default v2.1 rule:

> **Reuse widescreen architecture; do not redo widescreen research.**

## 1.3 `agluszak/whizzardry-8`

Role:

- long-term modern architecture reference;
- future native-Unicode engine candidate;
- UTF-8 / Unicode scalar / grapheme reference;
- modern SDL3/Vulkan compositor reference;
- alpha-overlay reference.

Why it is not the first PoC base:

- Linux is currently the primary verified platform;
- Windows remains less proven;
- architecture is changing quickly;
- current UI is still fixed-design-space oriented;
- it does not yet provide a ready scalable CJK renderer.

Therefore:

> **Do not switch P1 to Whizzardry 8. Keep it as a long-term candidate and oracle.**

## 1.4 `munument1/Wizardry8-KR`

Role:

- CJK localization oracle;
- proof that NPC dialog, items, descriptions, journal and CJK glyph mapping are practical;
- proof of Fan Patch 1.28-specific localization problems;
- source of lessons about minimal resource mutation.

Do not copy its packaging architecture by default. It patches multiple resources/binaries and therefore has higher file-level conflict risk with mods.

---

# 2. Product Definition

Wizardry8-ZH-TW is officially defined as:

> **A non-destructive high-resolution runtime Traditional Chinese localization Mod.**

Preferred user model:

```text
Wizardry 8
+ optional Widescreen
+ optional gameplay/content Mods
+ Wizardry8-ZH-TW
```

It is not a replacement game distribution.

## 2.1 Non-goals

The first release does not require:

- translating third-party Mods;
- translating arbitrary unknown user content;
- compatibility with every executable patch;
- replacing the full Wizardry 8 renderer;
- a full UAX #14 implementation;
- Fan Patch 1.28 support in the first PoC;
- perfect coexistence with every DLL loader on day one.

---

# 3. Non-Negotiable Design Principles

## 3.1 True High-Resolution Text

Forbidden:

```text
Chinese glyphs
    -> 640x480 UI surface
    -> upscale to 1920x1080
```

Required:

```text
logical UI coordinates
    -> physical coordinate mapping
    -> scalable glyph rasterization
    -> 32-bit alpha layer
    -> final renderer
```

At 1920x1080, glyphs must be rasterized for the physical output.

## 3.2 Runtime Translation Where Practical

Prefer:

```text
game/mod data
    -> original runtime text
    -> Translation Resolver
    -> translated presentation
```

over replacing whole files such as:

```text
ITEMS.DBS
FACT.DBS
STRINGDATA.DAT
NPC scripts
font STI resources
```

Direct resource patching is allowed only when runtime interception is impractical, the scope is narrow, the original is restorable, and conflict risk is documented.

## 3.3 Safe Fallback

Fallback is a complete presentation transaction, not merely a resolver return value.

Required cases:

| Situation | Required behavior |
|---|---|
| No translation entry or source fingerprint mismatch | Use the original text and the original presentation path |
| Translation matches, but font/layout/overlay preparation fails | Fall back to original text, preserve original layout/presentation, and record diagnostics |
| ZH-TW disabled | Resolver and high-resolution Chinese presentation path are both inactive |

Implementation rule:

> **Do not suppress the original game text until the translated presentation path is known to be usable for that draw/layout transaction.**

If translated presentation fails after a translation match, the system must restore or retain the original text and corresponding original layout path rather than leaving a blank region.

Never produce blank text, `???`, a crash, or an invented translation.

## 3.4 Mod-Safe Conservative Matching

Do not apply vanilla translation solely because an ID matches.

Preferred identity:

```text
stable resource identity
+
source fingerprint
+
optional context
```

If a Mod changes the source string, the fingerprint must no longer match and the Mod's source text must remain visible.

## 3.5 Feature Off = Original Behavior

Minimum configuration:

```ini
[ZH-TW]
Enabled=0
```

When disabled:

- no translation substitution;
- no high-res Chinese overlay;
- original text path remains visible;
- existing widescreen/gameplay behavior remains unchanged.

---

# 4. Target Runtime Architecture

```text
                    Wizardry 8
                        │
                active game content
                        │
           ┌────────────┴────────────┐
           │                         │
        Vanilla                  Gameplay Mod
           │                         │
           └────────────┬────────────┘
                        │
                  original text
                        │
                        ▼
              Translation Resolver
                        │
              ┌─────────┴─────────┐
              │                   │
       known vanilla text     unknown/modified
              │                   │
        zh-TW translation       original text
              │                   │
              └─────────┬─────────┘
                        ▼
                 CJK Text Layout
                        │
                        ▼
              High-Res Rasterizer
                        │
                        ▼
               32-bit Alpha Layer
                        │
                        ▼
                 Final Renderer
```

---

# 5. Translation Resolver

## 5.1 Encoding and Ownership Contract

The resolver contract must define encoding, length, and lifetime explicitly.

Preferred runtime contract:

```text
source text      = explicit UTF-8 view or adapter-defined source encoding
display text     = owned UTF-8 translation result
length           = explicit byte length; never implicit unbounded C-string ownership
lifetime         = result owns or references storage guaranteed valid through layout/render completion
```

If a hook receives UTF-16 / `wchar_t` / legacy byte text, the adapter must convert at a clearly defined boundary. Do not let mixed encodings leak into the resolver core.

Conceptual API:

```cpp
struct TranslationQuery {
    ResourceType type;
    StableResourceId resource_id;
    TextView source_text;
    TranslationContext context;
};

struct TranslationResult {
    bool translated;
    OwnedText display_text;
    TranslationDiagnostic diagnostic;
};
```

The concrete types may differ, but their encoding and lifetime guarantees must be documented.

Resolver behavior must be deterministic.

## 5.2 Match Contract

A translation is valid only when all required identity fields agree.

Recommended order:

```text
1. stable native resource identity
2. source fingerprint
3. required contextual discriminator
4. exactly one valid translation candidate
5. otherwise original text
```

If multiple candidates remain after required identity/context matching:

```text
ambiguous -> original text + diagnostic
```

Do not guess.

Do not use English source text alone as the long-term key if a stable identity is available.

## 5.3 Source Fingerprint

Default behavior is **exact source matching**.

Fingerprint must be captured:

> **before layout, wrapping, visual substitution, markup rewriting, or other presentation-side mutation.**

PoC may use SHA-256 or another deterministic hash.

Conceptual key:

```text
resource type
resource ID
source hash
required context
```

Examples:

```text
npc:42:dialog:108:<hash>
item:421:name:<hash>
```

If a gameplay Mod changes the source string, hash mismatch means:

```text
do not translate
use original Mod text
```

### Allowed normalization

Normalization is forbidden unless explicitly documented.

If later required, every allowed transformation must be listed individually, for example:

- line-ending normalization;
- removal of a proven non-semantic transport terminator;
- canonical handling of a documented engine control token.

Do not silently:

- trim arbitrary whitespace;
- fold punctuation;
- lowercase text;
- collapse multiple spaces;
- remove markup;
- normalize Unicode forms

unless a phase report proves that doing so is safe for that resource class.

## 5.4 Dynamic Text

For text containing dynamic parameters, P2A/P2 must determine whether the stable source is:

```text
template before expansion
```

or:

```text
final expanded text
```

Prefer template identity when the engine exposes it reliably.

If only expanded text is available, include sufficient context and document the limitation. Do not create a fingerprint strategy that breaks every time a numeric/name parameter changes.

## 5.5 Translation Data Failure

The following are resolver misses, not fatal errors:

- malformed translation file;
- duplicate key;
- invalid encoding;
- invalid required field;
- ambiguous candidate;
- source fingerprint mismatch;
- unsupported resource type.

Required behavior:

```text
original text + diagnostic
```

No malformed translation resource may prevent the original game text from rendering.

---

# 6. High-Resolution Renderer

## 6.1 Logical vs Physical Space

The game can retain its logical UI coordinate system.

ZH-TW maps:

```text
logical text position
    -> widescreen/canvas transform
    -> physical output position
```

Do not distort glyphs with non-uniform scale.

## 6.2 Rasterizer Abstraction

PoC:

```text
HiResTextRasterizerGDI
```

Long-term candidate:

```text
HiResTextRasterizerFreeType
```

Conceptual interface:

```cpp
class IHiResTextRasterizer {
public:
    virtual TextMetrics Measure(...) = 0;
    virtual RasterizedText Rasterize(...) = 0;
};
```

Do not scatter GDI calls through UI/gameplay code.

## 6.3 Why GDI First

Use GDI for P1 because it is:

- native on Windows;
- Unicode-capable;
- sufficient for Traditional Chinese;
- dependency-light;
- ideal for proving architecture before adding FreeType.

Do not trust DIB alpha to be correct automatically. Convert glyph coverage into explicit alpha before upload/composition.

---

# 7. CJK Layout

Western whitespace-only wrapping is insufficient.

Minimum required behavior:

- Unicode-aware measurement;
- break between normal Han characters;
- explicit newline support;
- clipping;
- scrolling;
- alignment;
- line-height control;
- basic Chinese punctuation protection.

Initial rules must at least avoid common opening punctuation at line end and closing punctuation at line start.

Full UAX #14 is not required for the first PoC.

---

# 8. Overlay Lifetime / Coordinates / Occlusion

High-resolution text must remain tied to the UI owner and coordinate context that created it.

Suggested retained-command concepts:

```cpp
TextOwnerId
TextScopeId
CoordinateSpace source_space
logical_bounds
logical_clip
draw_origin
anchor_context
zone_context
z_order
visible
owned_text
```

For every hook, P-1 must identify whether coordinates are:

```text
game coordinates
canvas coordinates
physical coordinates
```

Use existing widescreen drawing origins, anchors, and zone mappings rather than inventing parallel transforms.

A retained command must preserve enough coordinate context to replay correctly later. It must not assume that global draw origin, active zone, anchor, clip, or layout state is unchanged at replay time.

Rules:

```text
owner destroyed -> remove commands
dialog hidden -> hide/remove scope
screen switch -> clear irrelevant scope
scroll -> update position/clip
layout/anchor change -> update preserved coordinate context
modal shown -> translated text must obey the same intended occlusion relationship
```

Commands must own copies of their text. Do not retain unsafe external pointers.

## 8.1 Occlusion Constraint

Sorting translated commands relative to each other is **not sufficient** to guarantee correct ordering relative to original Wizardry 8 UI.

P1 may use fixed, intentionally topmost diagnostic text because it is only proving the physical-resolution overlay.

Before P2 begins, the architecture report must identify how real translated text will obey:

- popup/modal coverage;
- screen transitions;
- original UI layers;
- clipping;
- hidden panels.

If the chosen compositor cannot reproduce the required relationship, P2 is BLOCKED until an alternative integration point is demonstrated.

---

# 9. Loader / Hybrid Strategy

## 9.1 Baseline Pairing Is Atomic

The PoC baseline is not defined by one repository SHA alone.

P-1/P0 must pin and record:

```text
wiz8-widescreen repository revision
+
the exact decomp submodule revision referenced by that revision
+
required non-Git assets/tool inputs
+
retail executable hash
```

Do not casually mix a newer parent repository with an arbitrary decomp checkout.

Record any upstream-required workspace path, tool location, and non-Git asset acquisition procedure.

## 9.2 Hybrid Transplant Rules

When modifying an existing reconstructed game function:

- preserve required original function/address annotations;
- confirm that the function is present in the relevant transplant list;
- build/install the paired Hybrid outputs;
- produce runtime evidence that the modified path actually executed.

`wiz8hy.dll` and `wiz8hy_hooks.txt` must be treated as a paired artifact set for:

```text
build
install
backup
rollback
```

Do not update one without the other.

P-1 must name the concrete function(s)/hook point(s) proposed for P1.

P0/P1 must include an execution marker, log, or other deterministic proof that the new Hybrid code path is active. A successful build alone is not proof.

## 9.3 New ZH-TW Module State / ABI Rules

New ZH-TW code must use explicit initialize/shutdown boundaries.

Avoid hidden assumptions across the original executable / Hybrid DLL boundary.

Requirements:

- respect the existing CRT and ABI model;
- avoid passing allocator ownership across incompatible module boundaries unless the existing project explicitly supports it;
- do not add C++ object ownership to reconstructed binary layouts unless proven safe;
- prefer module-owned external state tables/maps for new retained state;
- keep new resources releasable on shutdown/reload;
- document any game-global pointer/reference retained by ZH-TW and its lifetime.

## 9.4 PoC Packaging

It is acceptable for the first PoC to integrate ZH-TW into the existing widescreen Hybrid build.

However, source code must remain a distinct module.

Recommended layout:

```text
src/zhtw/
include/zhtw/
translations/zh-TW/
docs/zhtw/
```

or, inside the decomp fork:

```text
src/wiz8/zh_text/
include/wiz8/zh_text/
```

## 9.5 Long-Term

Do not permanently define:

```text
ZH-TW == Widescreen feature
```

Desired model:

```text
Common Runtime / Loader
    ├─ Widescreen module
    └─ ZH-TW module
```

PoC may share `wiz8hy.dll`, but ZH-TW logic must be separable later.

Avoid creating a second incompatible `version.dll` loader.

---

# 10. Mod Compatibility Definition

The project does not promise universal compatibility.

It promises conservative behavior.

### Case A — Mod does not modify translated vanilla text

```text
expected -> Traditional Chinese
```

### Case B — Mod introduces new text

```text
expected -> original Mod text
```

### Case C — Mod modifies known vanilla text

```text
source fingerprint mismatch
expected -> original Mod text
```

### Case D — Mod changes gameplay data only

```text
expected -> ZH-TW should not interfere
```

### Case E — Mod replaces executable/DLL/hook points

```text
expected -> compatibility not guaranteed; dedicated adapter study required
```

---

# 11. Fan Patch 1.28 Policy

Fan Patch 1.28 is not treated as an ordinary content Mod.

It has executable/DLL-level changes and therefore requires a dedicated study.

Long-term desired architecture:

```text
              ZH-TW Core
                  │
          ┌───────┴────────┐
          │                │
Retail 1.24 Adapter    Fan Patch 1.28 Adapter
          │                │
      Wiz8.exe         Wiz8_v128.exe
```

Shared across adapters:

- translation data;
- resolver;
- CJK layout;
- high-resolution rasterizer;
- font configuration.

Only hook/integration details should differ.

---

# 12. Phase Plan

# P-1 — Architecture Adoption

## Goal

Confirm that v2.0 can be implemented using existing widescreen/hybrid architecture without recreating solved work.

## Review Targets

- `agluszak/wizardry-8-decomp`
- `abr17/wiz8-widescreen`
- `abr17/wizardry-8-decomp` branch `widescreen`
- `agluszak/whizzardry-8`
- `munument1/Wizardry8-KR`

## Questions

1. Where is the safest place to register a high-resolution UI overlay?
2. Which exact existing transform maps game/canvas coordinates to final output?
3. At each proposed hook, are coordinates game, canvas, or physical?
4. Which existing drawing origin, anchor, zone, and clip state must be preserved?
5. Which concrete Hybrid hook/function names are sufficient for P1?
6. Which functions must be present in the transplant list?
7. How will P1 prove at runtime that the transplanted path is actually active?
8. How can retained commands capture coordinate context without relying on later global state?
9. P1 diagnostic text may be intentionally topmost; what integration mechanism will P2 use so translated text is covered correctly by original popup/modal UI?
10. Can ZH-TW remain source-isolated?
11. Can ZH-TW be disabled without changing original behavior?
12. Does P1 require another `version.dll`? It should not.
13. Can P1 share the existing loader without creating a permanent dependency on widescreen logic?
14. What exact parent-repo revision / decomp-submodule revision pair forms the baseline?
15. What required workspace path, tool paths, and non-Git assets are part of that baseline?

## Deliverable

```text
docs/P-1_ARCHITECTURE_DECISION.md
```

Must include:

- exact repositories, branches, parent SHA, and paired decomp submodule SHA;
- required workspace path/tool assumptions and non-Git asset inputs;
- chosen overlay insertion point;
- **concrete proposed hook/function names**;
- transplant-list status for those hooks;
- coordinate space at every hook;
- exact existing transform/origin/anchor/zone mapping to reuse;
- retained-command coordinate-context strategy;
- P1 topmost diagnostic-layer decision;
- proposed P2 popup/modal occlusion strategy;
- loader decision;
- ABI/CRT/state ownership notes;
- source layout;
- known risks.

## Gate

`P-1 PASS` only if there is a concrete implementation path to P1 without inventing a new renderer/loader.

Otherwise:

`P-1 BLOCKED`

STOP.

---

# P0 — Windows Baseline Build

## Goal

Produce a clean reproducible local build/run of the chosen widescreen/hybrid baseline.

## Canonical Environment

```text
Windows 11
PowerShell 7
MSVC 2022 workflow used by wiz8-widescreen
CMake
existing repo toolchain
```

Do not invent a new WSL/Linux workflow unless source constraints require it.

## Record

- Windows version;
- MSVC version;
- PowerShell version;
- CMake version;
- wiz8-widescreen parent repo SHA;
- exact paired decomp submodule SHA;
- upstream-required workspace path;
- required tool paths;
- provenance/acquisition steps for required non-Git assets;
- original retail EXE SHA-256;
- runtime mode;
- Hybrid build/install commands;
- paired `wiz8hy.dll` + `wiz8hy_hooks.txt` install location;
- exact backup/rollback procedure for the Hybrid pair;
- baseline screenshot.

P0 must also establish one deterministic runtime marker proving that a deliberately modified/transplanted test path is executing. A successful compilation alone is insufficient.

## Formal Target

```text
1920x1080
```

Discovery may temporarily use another resolution, but formal P1 cannot pass at another resolution.

## Deliverables

```text
docs/P0_ENVIRONMENT.md
artifacts/p0/baseline-1920x1080.png
artifacts/p0/build-info.txt
```

## Gate

`P0 PASS` only when 1920x1080 baseline is reproducible.

Otherwise STOP.

---

# P1A — Physical-Resolution Alpha Transport Proof

## Goal

Prove a 32-bit alpha overlay can be composited at physical resolution, and characterize the actual alpha transport path.

Required:

```text
renderer  = 1920x1080
overlay   = 1920x1080
```

## Test A — Discrete Alpha Blocks

Render identical RGB blocks with alpha:

```text
0
64
128
192
255
```

This proves that transparency is not merely one-bit.

## Test B — 0..255 Alpha Ramp

Render a deterministic alpha ramp covering all 256 source alpha values over a known constant background color.

Record:

- source foreground RGB;
- background RGB;
- expected composite RGB for selected sample points;
- actual framebuffer/readback RGB;
- absolute per-channel error.

Do not require every adjacent alpha value to produce a unique final 8-bit RGB triplet if output quantization makes that impossible. The acceptance threshold must be derived from the actual formats in use.

## Alpha Contract

P1A must explicitly state whether the path uses:

```text
straight alpha
```

or:

```text
premultiplied alpha
```

and ensure the rasterizer/upload/compositor agree.

## Format Evidence

Record the format at each relevant stage:

```text
source surface
upload/staging representation
GPU texture
blend pipeline contract
final framebuffer/readback
```

If a conversion occurs, record it.

## Evidence

Use lossless PNG and/or direct framebuffer readback only. JPEG is not acceptable pixel evidence.

```text
artifacts/p1a-alpha/
    alpha-test-1920x1080.png
    alpha-ramp-1920x1080.png
    alpha-source.png
    alpha-pixels.txt
    render-info.txt
```

`alpha-pixels.txt` must include source, expected composite, actual readback, and error for representative alpha values.

## Gate

`P1A PASS` requires:

- alpha 0 is transparent;
- alpha 255 is opaque;
- intermediate alpha values composite distinctly;
- no one-bit cutoff behavior;
- documented straight/premultiplied contract;
- documented format path;
- quantitative readback consistent with the expected blend within a justified format/rounding tolerance.

Only claim **8-bit alpha transport preserved** if the source/upload/texture format evidence actually supports that claim.

Otherwise describe the narrower result precisely (for example, “smooth multi-level alpha works”) rather than overstating it.

Otherwise STOP.

---

# P1B — High-Resolution Traditional Chinese Proof

## Goal

Display true physical-resolution Traditional Chinese over the real game.

Required strings:

```text
巫術 8
繁體中文高解析文字測試
Wizardry 8 ZH-TW
```

Use GDI for PoC unless another existing path has clearly lower integration risk.

## Requirements

- raster target uses physical output resolution;
- Chinese is not drawn into the 640x480 game canvas;
- antialiasing is visible;
- original UI remains intact;
- original English path remains available;
- feature can be disabled;
- no gameplay/content DB files are modified.

## Evidence

```text
artifacts/p1b-hires-text/
    screenshot-1920x1080.png
    rasterizer-output.png
    crop-1x.png
    crop-nearest-upscaled.png
    render-info.txt
```

`crop-1x.png` must be a true 1:1 pixel crop from the final frame.

## Report

```text
docs/P1B_HIRES_TEXT_REPORT.md
```

Must explain logical coordinate, physical coordinate, font size mapping, raster size, alpha format, overlay layer, and why the result is not a 640x480 upscale.

## Gate

`P1B PASS` only when physical-resolution Chinese is proven.

Then:

> **STOP.**

Do not enter P2 without review.

---

# FIRST EXECUTION STOP GATE

The first Agent run is authorized for:

```text
P-1
P0
P1A
P1B
```

Nothing beyond that.

Do not:

- translate NPC dialog;
- translate items;
- translate journal;
- touch Fan Patch 1.28;
- build a complete translation DB;
- translate any third-party Mod;
- add FreeType unless it is strictly necessary to complete P1B.

---

# P2A — Stable Text Identity Probe

## Goal

Find a reproducible runtime identity for one real NPC dialog entry.

Choose one NPC and one deterministic English line.

Before final layout/rendering, log source-backed identity fields that actually exist.

The report must identify two exact observation points:

```text
A. where the stable key/identity is sampled
B. where the source text for fingerprinting is sampled
```

The source fingerprint must be captured before layout/wrapping/presentation mutation.

- NPC ID;
- script ID;
- topic/node ID;
- resource/string index;
- speaker;
- owner/callsite;
- original source text;
- source fingerprint.

Do not invent IDs.

Priority:

```text
1. native resource/string ID
2. script + node/topic identity
3. NPC + source-local index
4. fallback: source hash + context
```

Repeat after restart/reload. The same vanilla dialog must yield the same key.

Deliverable:

```text
docs/P2A_TEXT_IDENTITY_REPORT.md
artifacts/p2a/identity-log.txt
```

No P2 until this is reproducible.

---

# P2 — NPC Runtime Translation PoC

## Goal

Translate one real NPC conversation through the runtime resolver.

Flow:

```text
original NPC text
    -> stable identity
    -> source fingerprint
    -> Translation Resolver
    -> CJK layout
    -> high-res renderer
```

Translation resource must be external UTF-8 data.

Conceptual entry:

```json
{
  "npc:<identity>": {
    "sourceHash": "<hash>",
    "source": "Original text",
    "zh-TW": "繁體中文翻譯"
  }
}
```

Test:

- normal dialog;
- long dialog;
- scroll;
- clip;
- close/reopen;
- scene transition;
- modal popup over dialog;
- popup close.

No stale Chinese overlay may remain above hidden/covered UI.

## NPC Interaction Invariance

Translated presentation must not replace gameplay identity.

Required:

- a Chinese-displayed topic still maps to the original keyword/topic token;
- clicking/selecting a translated topic sends the original semantic identity to game logic;
- typed/topic interaction must not depend on the translated visible string unless explicitly designed and proven safe.

## Save Invariance Smoke Test

Run a short deterministic sequence:

```text
ZH-TW enabled
-> show translated NPC/UI text
-> perform one real interaction
-> save
-> close/disable ZH-TW
-> load save
-> confirm game state and interaction identity remain valid
```

Translation presentation must not become authoritative saved gameplay data unless the retail format explicitly stores that text and the plan has approved it.

---

# P2-M — Mod-Safe Smoke Test

## Goal

Prove conservative compatibility behavior.

This phase does **not** translate a Mod.

Test cases:

### 1. Vanilla unchanged text

```text
expected -> Traditional Chinese
```

### 2. Mod-added text

```text
expected -> original Mod text
```

### 3. Mod changes a known vanilla source string

```text
fingerprint mismatch
expected -> original Mod text
```

### 4. Gameplay-only Mod change

```text
expected -> gameplay behavior unchanged
```

Pass criteria:

- no crash;
- no `???`;
- no blank text;
- no accidental vanilla translation over changed Mod text;
- no destructive resource overwrite.

Deliverable:

```text
docs/P2M_MOD_SAFE_REPORT.md
```

---

# P3 — Items / Equipment / Descriptions

Extend the same resolver and renderer to:

- item names;
- equipment names;
- item descriptions;
- related tooltip/inspection text.

Do not create a separate ad-hoc translation system.

Mod-added or modified items must remain readable in their original text when no exact translation match exists.

Translated item names/descriptions must not change item IDs, inventory identity, save records, equipment references, or gameplay lookup keys.

Repeat the short enable -> interact -> save -> disable -> load invariance check for one translated item/equipment scenario.

---

# P4 — Journal

Translate journal content with robust long-form CJK layout.

Additional requirements:

- multi-line paragraphs;
- scrolling;
- clipping;
- punctuation handling;
- line height;
- correct logical-to-physical mapping.

Do not use Korean-style bitmap font replacement as the main architecture.

Journal translation is a presentation concern unless a specific retail save field proves otherwise. Do not accidentally write translated display text back into persistent journal/gameplay state.

Repeat the short enable -> view/interact -> save -> disable -> load invariance check for a representative journal scenario.

---

# P5 — Fan Patch 1.28 Compatibility Study

## Goal

Determine whether ZH-TW Core can support Fan Patch 1.28 through an adapter instead of duplicating the whole localization implementation.

Questions:

1. Which hook points differ?
2. Which loader/runtime components conflict?
3. Can a narrow `FanPatch128Adapter` be built?
4. Can translation data remain shared?
5. Can CJK layout remain shared?
6. Can the high-res renderer remain shared?
7. What version binding is unavoidable?

Deliverable:

```text
docs/P5_FANPATCH128_COMPATIBILITY.md
```

Do not promise 1.28 support before this phase passes.

---

# P6 — FreeType Evaluation

Evaluate replacing/supplementing GDI with FreeType.

Compare:

- build complexity;
- Windows packaging;
- font discovery;
- rendering quality;
- deterministic metrics;
- performance;
- portability to Whizzardry 8.

Do not replace a working GDI path merely for architectural purity.

---

# P7 — Packaging / Release Engineering

Provide:

- clean installer/package;
- enable/disable switch;
- uninstall instructions;
- no retail asset redistribution;
- only redistributable fonts;
- checksums;
- executable/version compatibility detection;
- safe refusal on unsupported versions.

Preferred behavior:

```text
unsupported executable build
    -> disable/refuse adapter safely
    -> never patch an unknown binary blindly
```

## 12.7A Technical Preview

A Technical Preview may be released when:

- representative NPC/item/journal scenarios work;
- install/uninstall is documented;
- ZH-TW disable path works;
- fallback is verified;
- basic Mod-safe smoke tests pass;
- known limitations are explicitly listed.

It is **not** a claim of full Traditional Chinese coverage.

## 12.7B Traditional Chinese Release Candidate

A localization Release Candidate additionally requires a separate content-quality specification covering:

- declared translation scope;
- coverage percentage by resource class;
- untranslated known vanilla content;
- terminology/glossary status;
- proofreading/review status;
- known layout exceptions;
- known missing/blocked resources.

P5 (Fan Patch 1.28 compatibility) and P6 (FreeType evaluation) are independent evaluation tracks.

They are not automatically required for the first Technical Preview or first localization Release Candidate unless the declared release scope explicitly includes them.

---

# 13. Source Layout

Recommended:

```text
Wizardry8-ZH-TW/
│
├─ src/
│   └─ zhtw/
│       ├─ TranslationResolver.cpp
│       ├─ TextIdentity.cpp
│       ├─ SourceFingerprint.cpp
│       ├─ HiResTextLayer.cpp
│       ├─ HiResTextLayout.cpp
│       ├─ HiResTextRasterizerGDI.cpp
│       └─ RuntimeAdapterRetail124.cpp
│
├─ include/zhtw/
├─ translations/zh-TW/
├─ fonts/README.md
├─ docs/
└─ artifacts/
```

If implemented inside the decomp fork, preserve the same logical isolation under `src/wiz8/zh_text/` or equivalent.

---

# 14. Configuration

## PoC Configuration

Keep the PoC configuration intentionally small:

```ini
[ZH-TW]
Enabled=1
DebugTextIdentity=0
```

Original-text fallback is mandatory behavior, not an optional user preference.

Do not expose these options until their semantics are fully defined and tested:

```text
FallbackToOriginal=0
HighResolutionText=0
```

A user must not be able to configure the PoC into a state where a translation failure produces blank/invalid presentation.

Future optional settings may include:

```ini
FontPath=
FontSizeScale=1.0
LogMissingTranslations=0
```

Do not expose unnecessary knobs during PoC.

---

# 15. Diagnostics

## Identity Logging

Log:

```text
resource type
stable ID
source fingerprint
source text preview
translation hit/miss
```

## Renderer Logging

Log:

```text
logical position
physical position
logical size
physical raster size
clip
output resolution
```

Missing translations may be logged, but the user-facing game must show original text.

---

# 16. Testing Philosophy

Avoid long burn-in tests.

Each phase must use:

- deterministic scenario;
- exact build SHA;
- exact executable hash;
- screenshot/evidence;
- short reproducible steps;
- expected result;
- actual result.

Prefer a short deterministic test over hours of unattended execution unless a specific lifetime/performance issue requires otherwise.

---

# 17. Regression Requirements

After every phase:

## ZH-TW Enabled

Verify:

- game starts;
- original UI still renders;
- target Chinese path works;
- no stale overlay;
- no crash.

## ZH-TW Disabled

Verify:

- resolver inactive;
- high-res Chinese overlay inactive;
- original text visible;
- widescreen behavior unchanged.

---

# 18. Artifact Requirements

Every phase stores evidence under:

```text
artifacts/<phase>/
```

Every report must include:

- repo SHA;
- decomp SHA;
- executable hash;
- build command;
- install command;
- launch command;
- modified file list;
- known issues;
- explicit PASS/BLOCKED decision.

---

# 19. Hard Failure Conditions

The Agent must stop and mark BLOCKED if:

- formal P1 cannot run at 1920x1080;
- the high-res overlay requires replacing gameplay/content DBs;
- Chinese is actually rendered at 640x480 then scaled;
- alpha is only one-bit transparency;
- disabling ZH-TW still changes displayed text;
- first PoC requires destructive modification of retail assets;
- a second incompatible `version.dll` is required with no coexistence path;
- the Agent cannot prove which render/text path is active.

Do not hide these failures with screenshots alone.

---

# 20. Success Definitions

## Technical Feasibility Success

```text
P1B PASS
```

Means only:

- true physical-resolution Traditional Chinese is visible;
- alpha transport/compositing evidence satisfies P1A;
- feature is disable-able;
- original game remains intact.

It does **not** mean runtime translation or full localization is solved.

## Runtime Translation Success

```text
P2 PASS
```

Means:

- a real NPC dialog is translated at runtime;
- identity/fingerprint are stable;
- layout/lifetime/occlusion are correct for the tested scenario;
- gameplay topic identity is preserved;
- the save-invariance smoke test passes.

## Mod-Safe Architecture Success

```text
P2-M PASS
```

Means:

- unknown Mod text remains readable;
- changed vanilla text is not mistranslated;
- gameplay Mod behavior remains intact for the tested cases.

## Technical Preview Readiness

Requires at least:

```text
P2
P2-M
representative P3
representative P4
packaging
disable/uninstall
fallback regression
basic save invariance
```

This is a **Technical Preview**, not a claim of complete localization coverage.

## Traditional Chinese Release Candidate Readiness

Requires all Technical Preview requirements plus a separately defined localization-content acceptance document specifying:

- translation scope;
- coverage;
- terminology authority;
- proofreading/review status;
- known omissions;
- known layout/content defects.

P5 and P6 are independent tracks and are required only if the declared release scope depends on them.

---

# 21. First-Agent Instruction

Give the Agent exactly this scope:

```text
You are implementing the first validation round of Wizardry8-ZH-TW Master Plan v2.1.

AUTHORIZED PHASES ONLY:
- P-1
- P0
- P1A
- P1B

DO NOT ENTER:
- P2A
- P2
- P2-M
- P3
- P4
- P5
- P6
- P7

Primary PoC base:
- abr17/wiz8-widescreen
- abr17/wizardry-8-decomp branch widescreen

Use agluszak/wizardry-8-decomp as behavioral/source oracle.
Use agluszak/whizzardry-8 only as modern architecture reference.
Use munument1/Wizardry8-KR only as localization/CJK oracle.

Primary goal:
Prove that true physical-resolution Traditional Chinese text can be composited over the real 1920x1080 Wizardry 8 runtime without rendering Chinese into the original low-resolution UI canvas.

Required outputs:
1. docs/P-1_ARCHITECTURE_DECISION.md
2. docs/P0_ENVIRONMENT.md
3. docs/P1A_ALPHA_REPORT.md
4. docs/P1B_HIRES_TEXT_REPORT.md
5. artifacts/p0/*
6. artifacts/p1a-alpha/*
7. artifacts/p1b-hires-text/*
8. exact build/install/run commands
9. modified-file list
10. known issues
11. final PASS/BLOCKED result for each phase

Mandatory behavior:
- Pin the wiz8-widescreen parent revision and its exact paired decomp submodule revision.
- Record required workspace/tool/non-Git asset assumptions.
- Name concrete P1 Hybrid hook/function candidates and confirm transplant-list status.
- Treat `wiz8hy.dll` and `wiz8hy_hooks.txt` as a paired build/install/rollback set.
- Produce runtime evidence that the new/transplanted path is actually active.
- Record whether each hook uses game, canvas, or physical coordinates and which existing transform/origin/anchor mapping is reused.
- P1 may use fixed topmost diagnostic text, but P-1 must document the proposed P2 popup/modal occlusion strategy.
- ZH-TW must be disable-able.
- No gameplay/content DB translation work in this round.
- No NPC translation in this round.
- No Fan Patch 1.28 work in this round.
- No third-party Mod translation in this round.
- Do not perform long burn-in tests.
- P1A must include discrete alpha blocks, a 0..255 alpha ramp, straight/premultiplied declaration, format-path evidence, and lossless/readback pixel evidence.
- Do not claim 8-bit alpha preservation unless the evidence supports that exact claim.
- Do not claim P1B PASS unless glyphs are proven to be rasterized for physical resolution rather than upscaled from 640x480.

After P1B evidence is produced:
STOP.
```

---

# 22. Final Project Decision

Proceed with v2.1 under this formal definition:

> **Wizardry8-ZH-TW is a non-destructive, high-resolution, runtime Traditional Chinese localization Mod.**

Short-term technical base:

```text
wiz8-widescreen / Hybrid
```

Behavior/source authority:

```text
wizardry-8-decomp
```

Long-term modern-engine reference:

```text
whizzardry-8
```

Compatibility rule:

```text
known unchanged vanilla -> Traditional Chinese
unknown/modded content -> original text
```

The project must not attempt to solve every Mod or Fan Patch version before proving the core runtime layer.

The next human review point is strictly after:

```text
P1B PASS
```

At that point, review the original-size 1920x1080 evidence and implementation report before authorizing NPC runtime translation.
