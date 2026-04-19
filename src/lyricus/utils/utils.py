from pathlib import Path
from typing import Optional
import re

from loguru import logger

from lyricus.utils.env import settings


def validate_path(path: Path, allowed_dirs: Optional[list[Path]] = None) -> Path:
    # 相対パスを絶対パスに変換
    if not path.is_absolute():
        path = (settings.BASE_DIR / path).resolve()
    else:
        path = path.resolve()
    
    if allowed_dirs is None:
        allowed_dirs = [settings.BASE_DIR]
    
    for allowed_dir in allowed_dirs:
        resolved_allowed = allowed_dir.resolve()
        try:
            # Pathオブジェクトの正しい比較方法
            if path.is_relative_to(resolved_allowed):
                return path
        except (ValueError, AttributeError):
            # is_relative_to が失敗した場合や、古いPythonバージョン対策
            try:
                # 文字列として比較するバックアップ案
                if str(path).startswith(str(resolved_allowed)):
                    return path
            except Exception:
                continue
    
    raise ValueError(f"安全でないパスが指定されました: {path}")


def ensure_output_path(output_path: Optional[Path] = None) -> Path:
    """
    出力パスを設定し、ディレクトリが存在しない場合は作成します。
    
    Args:
        output_path: 出力パス。指定がない場合はデフォルトのパスを使用します。
        
    Returns:
        Path: 設定された出力パス。
        
    Raises:
        ValueError: 安全でないパスが指定された場合。
    """
    if output_path is None:
        output_path = settings.OUTPUT_DIR
    
    # パスの安全性を検証
    validate_path(output_path)
    
    # ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.debug(f"出力パスを設定しました: {output_path}")
    return output_path


def ensure_abc_output_path(output_path: Optional[Path] = None) -> Path:
    """
    ABC ファイルの出力パスを設定します。
    
    Args:
        output_path: ABC ファイルの出力パス。
        
    Returns:
        Path: 設定された ABC ファイルのパス。
    """
    if output_path is None:
        # MIDI ファイルのパスから ABC ファイルのパスを生成
        # 実際には composer.py で管理されるべきですが、一時的な対応
        return settings.OUTPUT_DIR / "temp.abc"
    
    return ensure_output_path(output_path)


def write_file(path: Path, content: str, encoding: str = "utf-8") -> Path:
    """
    ファイルにテキストコンテンツを書き込みます。
    
    Args:
        path: 書き込み先のパス。
        content: 書き込むテキストコンテンツ。
        encoding: エンコーディング（デフォルト: utf-8）。
        
    Returns:
        Path: 書き込み先のパス。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    
    logger.debug(f"ファイルを保存しました: {path}")
    return path

def sanitize_error_message(error: Exception) -> str:
    """
    エラーメッセージから機密情報を除去します。
    
    Args:
        error: 例外オブジェクト。
        
    Returns:
        str: 安全なエラーメッセージ。
    """
    message = str(error)
    
    # API キーやトークンなどの機密情報を除去
    sensitive_patterns = [
        r'[A-Za-z0-9]{32,}',  # 長い文字列（API キーなど）
        r'Bearer\s+[A-Za-z0-9\-_\.]+',  # Bearer トークン
        r'api_key\s*=\s*["\'][A-Za-z0-9\-_\.]+["\']',  # API キーの文字列
    ]
    
    for pattern in sensitive_patterns:
        message = re.sub(pattern, '[REDACTED]', message)
    
    return message

def sanitize_prompt(prompt: str) -> str:
    """
    ユーザー入力を安全に処理します。
    
    Args:
        prompt: 入力されたプロンプト。
        
    Returns:
        str: 安全に処理されたプロンプト。
        
    Raises:
        ValueError: 安全でない入力が見つかった場合。
    """
    # 命令コードやスクリプトの注入を検出
    dangerous_patterns = [
        r'\$\{.*?\}',  # 変数展開
        r'\$\(',  # コマンド実行
        r'`.*`',  # バッククォートで囲まれたコマンド
        r'`.*`',  # バッククォートで囲まれたコマンド
        r'`.*`',  # バッククォートで囲まれたコマンド
        r'`.*`',  # バッククォートで囲まれたコマンド
        r'`.*`',  # バッククォートで囲まれたコマンド
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, prompt):
            raise ValueError("プロンプトに危険なパターンが含まれています。")
    
    # 文字数制限（LLM のトークン制限を考慮）
    if len(prompt) > 500:
        logger.warning(f"プロンプトが長すぎます（{len(prompt)}文字）。短くしてください。")
        prompt = prompt[:500]
    
    return prompt