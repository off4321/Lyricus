---

# CLAUDE.md

## Project: Lyricus
LLMを用いた高精度な音楽生成と、音楽理論に基づく自動評価（Metrics）フレームワーク。

## 🛠 技術スタック
- **Language**: Python 3.10+
- **LLM Engine**: Ollama (Remote/Local API)
- **Music Library**: music21
- **Audio Rendering**: FluidSynth
- **Notation**: ABC Notation

## 📂 ディレクトリ構成
ソースコードは `src/` レイアウトを採用。
```text
slyricus/
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

## 📝 コーディング・ドキュメント規約
- **Docstrings**: すべてのクラスおよび公開メソッドに **Google Style** の docstring を付与する。
  - 概要、Args（引数）、Returns（戻り値）、Raises（例外）を明記。
- **Naming**: 
  - クラス名: `PascalCase`
  - 関数・変数・ファイル名: `snake_case`
- **Typing**: 全ての関数に型ヒント（Type Hints）を付与する。
- **Error Handling**: `music21` のパースエラーやOllamaのAPI接続エラーは明示的にキャッチし、ログを出力する。

## 🎼 音楽的制約 (ABC Notation)
- LLMへの出力指示は「X:1から始まるABC記譜法のみ」に限定する。
- 解析には `music21.converter.parse()` を使用する。

## 🛠 コマンド (開発用)
- **Install dependencies**: `pip install -r requirements.txt`
- **Run POC**: `python src/lyricus/main.py`
- **Linting**: `flake8 src`

## 🎯 フェーズ1の目標
1. Ollamaとの安定した接続。
2. ABC記譜法の抽出（Sanitizer）と文法チェック（Syntax Metrics）。
3. MIDIファイルの書き出し。

---