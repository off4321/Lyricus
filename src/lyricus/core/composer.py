from pathlib import Path
from typing import Optional

from loguru import logger

from lyricus.core.llm_client import LLMClient
from lyricus.core.parser import Parser
from lyricus.utils.env import settings
from lyricus.utils.utils import ensure_output_path, ensure_abc_output_path, write_file, sanitize_error_message, sanitize_prompt


class Composer:
    """
    LLMを使用して音楽を生成し、MIDIファイルとして書き出すクラス。
    LLMClientとParserを組み合わせて、音楽生成パイプラインを実装します。
    """

    def __init__(self):
        """
        Composerを初期化します。
        """
        self.llm_client = LLMClient()
        self.parser = Parser()
        
        logger.info("Composerを初期化しました。")

    def generate_music(
        self,
        prompt: str,
        output_path: Optional[Path] = None,
        save_abc: bool = True,
    ) -> Path:
        """
        LLMにプロンプトを送信して音楽を生成し、MIDIファイルとして保存します。
        
        Args:
            prompt: 音楽を生成するための指示文。
            output_path: MIDIファイルの出力パス。指定がない場合はデフォルトのパスを使用します。
            save_abc: ABC記譜法を保存するかどうか。
            
        Returns:
            Path: 保存されたMIDIファイルのパス。
            
        Raises:
            RuntimeError: 音楽の生成や保存に失敗した場合。
        """
        # 入力の検証
        try:
            safe_prompt = sanitize_prompt(prompt)
        except ValueError as e:
            logger.error(f"プロンプトの検証に失敗しました: {e}")
            raise ValueError(f"プロンプトの検証に失敗しました: {e}")
        
        # 音楽の生成
        try:
            # 1. ABC記譜法の生成
            abc_text = self.llm_client.generate_abc_notation(prompt)
            
            # 2. ABC記譜法の解析
            score = self.parser.parse_abc_to_score(abc_text)
            
            # 3. メタデータの抽出
            metadata = self.parser.extract_metadata(score)
            logger.info(f"メタデータを抽出しました: {metadata}")
            
            # 4. MIDIファイルの保存
            midi_path = self._save_midi(score, output_path)
            
            # 5. ABC記譜法の保存（オプション）
            if save_abc:
                abc_path = self._save_abc(abc_text, output_path)
                logger.info(f"ABC記譜法を保存しました: {abc_path}")
            
            logger.info(f"音楽の生成と保存に成功しました: {midi_path}")

            score.write('midi', fp=str(output_path))
            logger.info(f"MIDIファイルを正常に書き出しました: {output_path}")
            return midi_path
            
        except Exception as e:
            logger.error(f"音楽の生成に失敗しました: {sanitize_error_message(e)}")
            raise RuntimeError(f"音楽の生成に失敗しました: {sanitize_error_message(e)}")

    def _save_midi(self, score, output_path: Optional[Path] = None) -> Path:
        """
        楽譜オブジェクトをMIDIファイルとして保存する内部メソッド。
        
        Args:
            score: music21のScoreオブジェクト。
            output_path: MIDIファイルの出力パス。
            
        Returns:
            Path: 保存されたMIDIファイルのパス。
        """
        # 出力パスの設定
        output_path = ensure_output_path(output_path)
        
        # MIDIファイルとして保存
        score.write("midi", fp=output_path)
        
        logger.info(f"MIDIファイルを保存しました: {output_path}")
        return output_path

    def _save_abc(self, abc_text: str, output_path: Optional[Path] = None) -> Path:
        """
        ABC記譜法をテキストファイルとして保存する内部メソッド。
        
        Args:
            abc_text: 保存するABC記譜法テキスト。
            output_path: ABCファイルの出力パス。
            
        Returns:
            Path: 保存されたABCファイルのパス。
        """
        # 出力パスの設定
        output_path = ensure_abc_output_path(output_path)
        
        # ABCファイルとして保存
        write_file(output_path, abc_text, encoding="utf-8")
        
        return output_path