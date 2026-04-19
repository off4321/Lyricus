import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env ファイルの読み込み（機密情報の保護）
# 絶対パスで指定し、パスを正しく設定
# env.py のパス: /app/src/lyricus/utils/env.py
# 親ディレクトリ: /app/src/lyricus/utils → /app/src/lyricus → /app/src → /app
env_file_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_file_path, override=True)

class EnvConfig(BaseSettings):
    """
    Lyricus プロジェクト全体の環境変数を管理する設定クラス。
    pydantic-settings を使用して、型安全に値を保持します。
    """
    
    # プロジェクトのルートディレクトリ設定
    BASE_DIR: Path = Field(
        default=Path(__file__).resolve().parent.parent.parent.parent,
        description="プロジェクトのルートディレクトリ"
    )
    
    # Ollama 関連の設定
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama API のベース URL"
    )
    OLLAMA_MODEL: str = Field(
        default="llama3",
        description="使用する LLM モデル名"
    )
    
    # 機密情報の管理（API キーなど）
    OLLAMA_API_KEY: Optional[str] = Field(
        default=None,
        description="Ollama API キー（必要に応じて）"
    )
    
    # 音楽生成・保存パスの設定
    OUTPUT_DIR: Path = Field(
        default=Path("output"),
        description="生成された音楽ファイルの出力先"
    )
    SOUNDFONT_PATH: Optional[Path] = Field(
        default=None,
        description="FluidSynth で使用する SoundFont(.sf2) のパス"
    )

    # ログレベルの設定
    LOG_LEVEL: str = Field(
        default="INFO",
        description="loguru のログレベル (DEBUG, INFO, ERROR 等)"
    )

    # pydantic の設定: .env ファイルを優先的に読み込む
    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        extra="ignore",  # 定義外の環境変数は無視する
        env_prefix="LYRICUS_",  # 環境変数のプレフィックスを設定
    )

def get_config() -> EnvConfig:
    """
    環境設定のインスタンスを取得し、初期設定（ディレクトリ作成など）を行います。
    
    Returns:
        EnvConfig: 初期化済みの設定インスタンス
    """
    config = EnvConfig()
    
    # 出力ディレクトリを絶対パスに変換
    if not config.OUTPUT_DIR.is_absolute():
        config.OUTPUT_DIR = config.BASE_DIR / config.OUTPUT_DIR
        
    # 出力ディレクトリが存在しない場合は作成
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # ログレベルの設定反映（簡易版）
    logger.info(f"Lyricus 環境設定を読み込みました。")
    logger.info(f"Model: {config.OLLAMA_MODEL}")
    logger.info(f"OUTPUT_DIR: {config.OUTPUT_DIR}")
    logger.info(f"BASE_DIR: {config.BASE_DIR}")
    
    return config

# シングルトン的に利用するためのグローバルインスタンス
settings = get_config()