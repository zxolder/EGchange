# Screen Translator (English → Chinese, one-hotkey)

按一個熱鍵，就把當下螢幕上偵測到的英文文字截圖、辨識、翻譯成中文，並疊加顯示在原文位置附近。適合玩英文遊戲、看英文網頁或任意程式時快速理解畫面文字。

僅支援 **Windows 10/11**（使用 Windows 內建 OCR 引擎）。

## 運作方式

1. 按下熱鍵（預設 `Ctrl+Alt+T`）
2. 擷取整個虛擬螢幕畫面
3. 用 Windows 內建的 OCR 引擎辨識英文文字與座標
4. 把辨識出的文字丟給翻譯引擎轉成中文
5. 在螢幕上原文位置疊加顯示半透明色塊 + 中文翻譯
6. 幾秒後自動消失，或再按一次熱鍵 / `Esc` 手動收起

## 安裝

需求：Windows 10/11、Python 3.9+，且系統要有安裝「英文」OCR 語言套件（通常英文版 Windows 內建就有；若沒有：設定 → 時間與語言 → 語言與地區 → 新增語言，或「選用功能」→「新增功能」搜尋 English OCR）。

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

依需求編輯 `.env`（熱鍵、目標語言、翻譯引擎等）。

## 執行

```powershell
python -m screen_translator.main
```

保持這個主控台視窗開著，切到遊戲或任意程式，按下熱鍵即可翻譯當下畫面。

> 部分遊戲的全域熱鍵擷取需要以**系統管理員身分執行**（尤其遊戲本身以系統管理員權限啟動、或有反作弊機制時）。若熱鍵沒反應，試著以系統管理員身分開啟終端機再執行。

## 翻譯引擎設定

`.env` 中的 `TRANSLATE_ENGINE` 可選：

| 值 | 說明 |
|---|---|
| `google`（預設） | 使用免費的 Google 翻譯端點，不需申請金鑰，適合先試用；但屬非官方端點，量大時可能被限速 |
| `deepl` | 需要 `DEEPL_API_KEY`（DeepL 免費方案可申請），翻譯品質通常較好、較穩定 |
| `microsoft` | 需要 `MS_TRANSLATOR_KEY`（Azure Translator 資源），另可設定 `MS_TRANSLATOR_REGION` |
| `gemini` | 需要 `GEMINI_API_KEY`（Google AI Studio / Gemini API 金鑰），用 LLM 翻譯，理解上下文能力較好；可用 `GEMINI_MODEL` 指定模型（預設 `gemini-2.5-flash`） |

## 打包成 exe（下載即可用，不需裝 Python）

有兩種方式取得 `ScreenTranslator.exe`：

### 方式一：GitHub Actions 自動編譯（推薦）

1. 推一個版本標籤到這個 repo，例如：
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
2. GitHub Actions 會自動在 Windows 雲端機器上打包，完成後：
   - 到 repo 的 **Releases** 頁面下載 `ScreenTranslator.exe`（標籤觸發會自動建立 Release）
   - 或不想打標籤的話，到 **Actions** 分頁手動觸發 `Build Windows EXE` workflow（`workflow_dispatch`），完成後在該次執行的 **Artifacts** 下載 `ScreenTranslator-windows.zip`

### 方式二：自己在 Windows 上打包

```powershell
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build.spec
```

打包完成後執行檔在 `dist\ScreenTranslator.exe`。

### 使用打包好的 exe

1. 把 `.env.example` 複製一份到 exe **同一個資料夾**，改名成 `.env`，依需求編輯設定
2. 直接雙擊 `ScreenTranslator.exe`（或用系統管理員身分執行，理由同上）
3. 保持主控台視窗開著，切到遊戲/程式，按熱鍵翻譯畫面

## 已知限制

- **全螢幕獨佔模式（exclusive fullscreen）的 DirectX 遊戲**可能無法被一般截圖 API 擷取到畫面；把遊戲改成「視窗模式」或「無邊框視窗模式」通常就能正常運作。
- OCR 準確度取決於畫面文字的清晰度與背景複雜度；遊戲中的特效字體、低對比背景可能辨識失敗或不準確。
- 疊加視窗上有文字的區域是不透明色塊，滑鼠移到該區域時點擊會點到疊加視窗而非底下的遊戲/程式；這也是為何預設會在幾秒後自動消失（可用 `AUTO_HIDE_SECONDS` 調整，設 `0` 則不自動消失，改用熱鍵/`Esc`手動收起）。
- 多螢幕、不同 DPI 縮放比例混用時，疊加位置可能有些微偏移。
- 免費 Google 翻譯端點沒有官方 SLA，若頻繁使用建議改用 `deepl` 或 `microsoft` 並申請自己的 API 金鑰。

## 專案結構

```
screen_translator/
  capture.py    # 螢幕截圖 (mss)
  ocr.py        # Windows 內建 OCR (winsdk)
  translate.py  # 翻譯後端抽象層 (deep-translator)
  overlay.py    # 透明疊加視窗 (tkinter)
  config.py     # 從環境變數讀取設定
  main.py       # 進入點：全域熱鍵 + 主流程
```
