import argparse
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from lyricus.core.composer import Composer
from lyricus.core.llm_client import LLMClient
from lyricus.core.parser import Parser
from lyricus.metrics.syntax import ABCSyntaxMetric, ABCStructureMetric
from lyricus.metrics.base import CompositeMetric
from lyricus.utils.env import settings
from lyricus.utils.utils import ensure_output_path


def parse_arguments() -> argparse.Namespace:
    """
    コマンドライン引数をパースします。
    
    Returns:
        argparse.Namespace: パースされた引数。
    """
    parser = argparse.ArgumentParser(
        description="Lyricus - LLM による音楽生成フレームワーク",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python -m lyricus.main --prompt "悲しいピアノの曲"
  python -m lyricus.main --prompt "明るいポップス" --no-save-abc
  python -m lyricus.main --prompt "ジャズ風の曲" --metrics
        """
    )
    
    # プロンプト引数
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="音楽を生成するための指示文"
    )
    
    # 出力パス引数
    parser.add_argument(
        "--output",
        type=str,
        help="MIDI ファイルの出力パス（デフォルト: output/output.mid）"
    )
    
    # ABC 保存オプション
    parser.add_argument(
        "--no-save-abc",
        action="store_true",
        help="ABC 記譜法の保存をスキップする"
    )
    
    # メトリクス評価オプション
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="音楽生成後にメトリクス評価を実行する"
    )
    
    # モデル指定オプション
    parser.add_argument(
        "--model",
        type=str,
        help="使用する Ollama モデル名（デフォルト: env.py の設定）"
    )
    
    return parser.parse_args()


def generate_music(
    prompt: str,
    output_path: Optional[Path] = None,
    save_abc: bool = True,
    metrics: bool = False,
    model: Optional[str] = None,
) -> Path:
    """
    音楽を生成し、必要に応じて評価を行います。
    
    Args:
        prompt: 音楽を生成するための指示文。
        output_path: MIDI ファイルの出力パス。
        save_abc: ABC 記譜法を保存するかどうか。
        metrics: メトリクス評価を実行するかどうか。
        model: 使用する Ollama モデル名。
        
    Returns:
        Path: 保存された MIDI ファイルのパス。
        
    Raises:
        RuntimeError: 音楽の生成や評価に失敗した場合。
    """
    # 出力パスの設定と検証
    output_path = ensure_output_path(output_path)
    
    # コンポーザーの初期化
    composer = Composer()
    
    # 音楽の生成
    midi_path = composer.generate_music(
        prompt=prompt,
        output_path=output_path,
        save_abc=save_abc,
    )
    
    # メトリクス評価の実行（オプション）
    if metrics:
        _evaluate_music(composer, midi_path)
    
    return midi_path


def _evaluate_music(composer: Composer, midi_path: Path) -> None:
    """
    生成された音楽をメトリクスで評価します。
    
    Args:
        composer: Composer インスタンス。
        midi_path: 評価対象の MIDI ファイルパス。
        
    Raises:
        RuntimeError: 評価に失敗した場合。
    """
    try:
        # ABC テキストの読み込み
        abc_path = midi_path.with_suffix(".abc")
        if not abc_path.exists():
            logger.warning(f"ABC ファイルが見つかりません: {abc_path}")
            return
        
        abc_text = abc_path.read_text(encoding="utf-8")
        
        # メトリクスの初期化
        syntax_metric = ABCSyntaxMetric()
        structure_metric = ABCStructureMetric()
        
        # コンポジットメトリクスの作成
        metrics_list = [syntax_metric, structure_metric]
        composite_metric = CompositeMetric(metrics_list)
        
        # 楽譜オブジェクトの解析
        score = composer.parser.parse_abc_to_score(abc_text)
        
        # 評価の実行
        results = composite_metric.calculate(score)
        
        # 評価結果の出力
        logger.info("=" * 60)
        logger.info("音楽評価結果")
        logger.info("=" * 60)
        
        for metric_name, result in results.items():
            logger.info(f"{metric_name}: {result['value']:.2f}%")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"音楽評価に失敗しました: {e}")
        raise RuntimeError(f"音楽評価に失敗しました: {e}")


def main() -> int:
    """
    メインエントリーポイント。
    
    Returns:
        int: エラーコード（0: 成功、1: 失敗）
    """
    try:
        # 引数のパース
        args = parse_arguments()
        
        # 出力パスの設定
        output_path = Path(args.output) if args.output else None
        
        # 音楽の生成
        midi_path = generate_music(
            prompt=args.prompt,
            output_path=output_path,
            save_abc=not args.no_save_abc,
            metrics=args.metrics,
            model=args.model,
        )
        
        logger.info(f"音楽生成が完了しました: {midi_path}")
        return 0
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())