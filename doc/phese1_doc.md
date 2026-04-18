**Lyricus フェーズ1 内部設計書**

フェーズ1の目的は、「LLMからのテキスト生成」から「MIDIファイルの出力」までを、エラー耐性を持たせた状態で貫通させることです。

---

## 1. システムアーキテクチャ
フェーズ1では、以下の3つの主要コンポーネントを実装します。

| コンポーネント | 役割 | 主要ライブラリ |
| :--- | :--- | :--- |
| **`LLMClient`** | Ollama APIとの通信、プロンプト管理 | `requests` |
| **`ABCProcessor`** | テキストからのABC抽出、文法バリデーション | `re`, `music21` |
| **`AudioExporter`** | MIDI生成、WAV変換（オプション） | `music21`, `fluidsynth` |

---

## 2. モジュール詳細設計

### 2.1 `LLMClient` (core/llm_client.py)
OllamaのREST APIをラップし、音楽生成に最適化されたパラメータを保持します。

* **メソッド:** `generate(prompt: str) -> str`
* **システムプロンプト:**
    > "あなたは音楽家です。回答は必ずABC記譜法（ABC Notation）のみで行ってください。説明や挨拶は一切禁止します。出力は 'X:1' から始めてください。"
* **パラメータ:**
    * `model`: "gemma2:2b" (または指定のモデル)
    * `temperature`: 0.7 (創造性と構造保持のバランス)
    * `stream`: False (フェーズ1では一括受信)

### 2.2 `ABCProcessor` (core/parser.py)
LLMの出力から純粋なABCデータを抽出し、音楽理論ライブラリで扱える形式に変換します。

* **Sanitization (洗浄):** * 正規表現 `r"(X:1[\s\S]*)"` を用いて、不要な前口上をカットします。
* **Validation (検証):**
    * `music21.converter.parse()` を呼び出し、パースエラー（`music21.converter.ConverterException`）をキャッチします。
    * エラー時は例外をスローし、Composer側で再試行（リトライ）のフラグを立てます。

### 2.3 `AudioExporter` (utils/audio.py)
データ構造から物理ファイルへの変換を担います。

* **MIDI出力:** `score.write('midi', fp=filepath)`
* **WAV出力:** `subprocess` を用いて `fluidsynth` コマンドを実行。
    * コマンド案: `fluidsynth -ni {sf2_path} {midi_path} -F {wav_path} -r 44100`

---

## 3. データフロー

1.  **Input:** ユーザーからの指示（例：「明るい4小節のメロディ」）
2.  **Request:** `LLMClient` がシステムプロンプトを付与して Ollama API へ送信
3.  **Receive:** LLMがテキストを返却
4.  **Extract:** `ABCProcessor` が `X:1` 以降を抽出
5.  **Parse:** `music21` オブジェクトに変換
    * **NG:** 文法エラーならエラー内容をログし、終了（または再試行）
    * **OK:** 次へ
6.  **Export:** `AudioExporter` が `.mid` と `.wav` を生成
7.  **Output:** 物理ファイルとしての保存完了

---

## 4. フェーズ1のディレクトリ構成（再掲・詳細化）

```text
lyricus/
├── pyproject.toml      # プロジェクトの設定・依存関係
├── README.md           # プロジェクト説明
├── .gitignore          # 
├── src/
│   └── lyricus/        # パッケージ本体
│       ├── __init__.py
│       ├── main.py     # エントリーポイント
│       ├── core/
│       │   ├── __init__.py
│       │   ├── llm_client.py
│       │   └── parser.py
│       └── utils/
│           ├── __init__.py
│           └── audio.py
├── tests/              # テストコード
└── exports/            # 生成物の出力先 (Git管理外)
```

---

## 5. 異常系処理（フェーズ1の要）

精度を担保するために、以下のエラーパターンを想定して実装します。

* **API接続エラー:** Ollamaサーバーが未起動の場合、分かりやすいエラーメッセージを表示。
* **空レスポンス:** LLMが何も返さなかった場合、再生成を促す。
* **不完全なABC:** `X:1` はあるが、小節線 `|` がない、または途中で切れている場合、`music21` のパース失敗として検知。

---
