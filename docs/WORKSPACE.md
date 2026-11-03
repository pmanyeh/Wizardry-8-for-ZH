# 本機工作區配置

上游實體目錄：`D:\git\Wizardry 8 for zh\local\wiz8-ws`。

此目錄包含主 repository、`decomp` / MinHook submodules、portable tools、建置快取、release assets、`games/reference` 與 `games/work` 測試副本。`local/` 已由本專案 `.gitignore` 排除；不會把遊戲資料、工具或巢狀 Git repository 加入外層專案。

上游仍有腳本與 CMake 快取使用 `C:\dev\wiz8-ws`。該路徑保留為 directory junction，指向上述實體目錄。decomp 的 gitdir/worktree 已改為相對設定，可直接由專案內的新位置操作 Git。這是本機相容入口，並不表示已將所有上游腳本改造成可攜版本。

搬移前已逐檔比對 23,736 個檔案（7,875,211,233 bytes）的 SHA-256，全部一致。系統自動核准檢查阻擋了刪除舊實體副本的動作，因此改為保留 `C:\dev\wiz8-ws.relocation-backup` 作為回復備份；它仍佔用原來的 C 槽空間，但不是後續工作的目錄。新工作目錄位於 D 槽。

## 繼續建置

在專案根目錄的 PowerShell 執行：

```powershell
. .\scripts\Enter-Upstream.ps1
```

這會進入相容入口並載入上游當次 session 的 portable tools。接著可執行原有建置命令：

```powershell
.\build.ps1
powershell -NoProfile -File scripts\build\build-decomp.ps1
powershell -NoProfile -File scripts\hybrid\build_hybrid.ps1
```

從 IDE 編輯 `local/wiz8-ws` 的原始碼即可；它與相容入口是相同檔案。為了沿用現有建置快取，建置命令從相容入口執行。

## 保留的進度

- 主 repo baseline：`7a0757a0ea9a0b03693a48a805485c892e07def0`。
- decomp baseline：`ca63d4447a973815670fbf6e146110e5d46989f5`。
- 分支：兩個 repo 都是 `zh-tw-hires-poc`。
- P0-B 執行標記與成對回復驗收已 PASS。一次性標記已由 P1 的薄掛點取代。
- `build/zhtw/p0-baseline` 保留乾淨 P0-A 的 loader / Hybrid / hooks；不與 probe 產物混淆。
- 使用者恢復 computer-use 後，P1A 與 P1B 已 PASS。報告見 `P1A_ALPHA_REPORT.md` 與 `P1B_HIRES_TEXT_REPORT.md`；首輪完成，未進入 P2A。
- 最新測試 binaries 在 `build/zhtw/p1b`；測試副本目前為 `Enabled=0`。測試程式已正常退出。

原始 Steam 安裝仍在 `D:\SteamLibrary\steamapps\common\Wizardry8`，未搬移或修改。既有 baseline artifacts 中的舊路徑屬於當時的實際紀錄，予以保留；搬移證據另外記在 `artifacts/workspace-relocation/`。
