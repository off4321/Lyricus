# Lyricus プロジェクト定義書

## 1. プロダクト概要
**Lyricus** は、LLM（Large Language Models）を用いた高精度な音楽生成と、音楽理論に基づく自動評価（Metrics）を組み合わせたPythonフレームワークです。

---

## 2. 機能一覧 (Feature List)

| 大項目 | 中項目 | 小項目（具体的な実装機能） | 優先度 |
| :--- | :--- | :--- | :---: |
| **1. LLM Interaction** | **Adapter** | Ollama APIとの接続・モデル選択機能 | ★★★ |
| | **Prompting** | ABC記譜法に特化したシステムプロンプトの設計 | ★★★ |
| | **Sanitizer** | LLM回答からABC部分（X:1~）のみを抽出する正規表現処理 | ★★★ |
| **2. Evaluator** | **Syntactic** | `music21`を用いたABC文法のパースチェック | ★★★ |
| | **Theoretical** | スケール適合率（Key指定の音か）の数値化 | ★★☆ |
| | **Heuristic** | 音の跳躍（Leap）や音域（Range）の妥当性評価 | ★★☆ |
| | **Rhythm** | 拍子と小節内の音符長の整合性チェック | ★★☆ |
| **3. Feedback Loop** | **Refinement** | 評価エラーを自然言語でLLMへフィードバックする機能 | ★★☆ |
| | **Iteration** | 合格スコアに達するまでの自動再生成ロジック | ★★☆ |
| **4. Processing** | **Transcriber** | ABC ➡ MIDI / MusicXML への変換 | ★★★ |
| | **Renderer** | FluidSynthを用いたWAVオーディオの生成 | ★☆☆ |
| | **Visualizer** | 楽譜（PNG/PDF）の画像レンダリング | ★☆☆ |
| **5. Packaging** | **CLI/API** | コマンドラインUI / FastAPIによるAPIエンドポイント | ★☆☆ |
| | **Metrics API** | 外部から独自の評価関数を追加できるプラグイン機構 | ★☆☆ |

---

## 3. フェーズ1 実装計画 (MVP: Minimum Viable Product)

フェーズ1では、**「プロンプトから音が出るまでの一本道を、高い信頼性で構築する」**ことを目標とします。

### 3.1 開発目標
- Ollama上の `gemma4:e4b` 等から安定してABC記譜法を取得する。
- 取得したデータを `music21` で読み込み、文法エラーを検知する。
- 成功時にMIDIファイルを生成し、ローカル環境で再生可能にする。

### 3.2 フェーズ1の実装タスク詳細

#### タスク1: LLM Connector の作成
- `requests` を用いたOllama API クライアントの実装
- モデル名、温度パラメータ（Temperature）の設定機能
- ABC記譜法を強制するシステムプロンプトの定義

#### タスク2: ABC Parser & Sanitizer の作成
- マークダウン（```abc ... ```）や余計な解説テキストを排除する正規表現の実装
- `music21.converter.parse()` による文法チェック

#### タスク3: Basic Evaluator の作成
- 「パースに成功したか（Syntax OK/NG）」のみを判定する最初の評価器
- エラー発生時に内容（トレースバック等）をログ出力する機能

#### タスク4: MIDI Exporter の作成
- 正常にパースされたオブジェクトを `.mid` ファイルとして保存する機能
- FluidSynthを用いたWAV変換ユーティリティ（PoCコードの移植）

---

## 4. ディレクトリ構成（案）

```
lyricus/
├── README.md
├── pyproject.toml        # プロジェクト管理・依存関係
├── .gitignore
├── exports/              # 生成されたMIDI/WAVの保存先（非公開）
│   └── .gitkeep
└── src/
    └── lyricus/          # メインパッケージ
        ├── __init__.py
        ├── main.py       # CLIエントリーポイント
        ├── core/         # ロジック基盤
        │   ├── __init__.py
        │   ├── composer.py
        │   ├── llm_client.py
        │   └── parser.py
        ├── metrics/      # 評価・精度管理
        │   ├── __init__.py
        │   ├── base.py
        │   └── syntax.py
        └── utils/        # ユーティリティ
            ├── __init__.py
            ├── audio.py
            └── visualizer.py
```

---