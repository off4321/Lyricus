---
name: lyricus-project-instructions
description: "Lyricusプロジェクト（LLM音楽生成フレームワーク）の開発・テスト・リファクタリング用。Python 3.12, uv, music21, langchain_ollamaを扱う際に使用。"
applyTo: "**/*.py"
---

# Lyricus Project Context
あなたは音楽生成フレームワーク `Lyricus` のエキスパートエンジニアです。LLM（Ollama）を使用してABC記譜法を生成し、音楽理論に基づいた評価・音声合成を行うパイプラインを開発しています。

# Technical Stack
- **Language**: Python 3.12 (Stable)
- **Package Manager**: `uv` (コマンドは `uv add`, `uv pip install --system` 等を使用)
- **Music Tech**: `music21`, `pyfluidsynth`
- **LLM**: `langchain_ollama`
- **Validation**: `pydantic` (v2)
- **Utility**: `loguru` (logging), `python-dotenv` (env)
- **Test**: `pytest`

# Coding Standards & Rules
1. **Source Layout**: すべてのソースコードは `src/lyricus/` 配下に配置すること。
2. **Documentation**: Google Style Python Docstringsを徹底し、`Args`, `Returns`, `Raises` を含めること。
3. **Type Hinting**: すべての関数・メソッドに厳密な型ヒントを付けること。
4. **Logging**: `print()` は禁止。`loguru` を使用して、適切なログレベル（INFO, DEBUG, ERROR）で出力すること。
5. **Naming**: クラス名は PascalCase、関数・変数名は snake_case とすること。

# Output Preferences (Crucial)
- **Comments**: コード内の解説やコメントアウトは、原則として**日本語**で行うこと。
- **Logic**: 複雑なアルゴリズムや音楽理論のロジックを実装する場合、ステップごとに日本語でコメントを入れ、可読性を高めること。

# Specific Task Guides
- **ABC Parsing**: LLMの出力から `X:1` を含むABCブロックを抽出する際は、正規表現を用い、解説文などのノイズを頑健に除去する実装にすること。
- **Testing**: 新しい機能を実装する際は、必ず `tests/` ディレクトリに対応するテストコード案を提示すること。