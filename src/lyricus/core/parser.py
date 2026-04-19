from typing import Optional
from music21 import converter, stream, environment
from loguru import logger
import os
import re
import tempfile

from lyricus.utils.env import settings


class Parser:
    """
    ABC記譜法を解析し、音楽情報を抽出するクラス。
    music21ライブラリを使用して、ABC記譜法を楽譜オブジェクトに変換します。
    """

    def __init__(self):
        """
        Parserを初期化します。
        """
        logger.info("Parserを初期化しました。")
        
    def parse_abc_to_score(self, abc_text: str):
        """
        ABC記譜法をmusic21のScoreオブジェクトに変換します。
        一時ファイルを経由することで、解析の安定性を向上させています。
        
        Args:
            abc_text: 変換対象のABC記譜法テキスト。
            
        Returns:
            music21.stream.Score: 変換された楽譜オブジェクト。
            
        Raises:
            ValueError: ABC記譜法の解析に失敗した場合。
        """
        # music21 の警告がうるさい場合は一時的に抑制（任意）
        # env = environment.Environment()
        # env['warnings'] = 0

        tmp_file_path = None
        try:
            # 1. 強力なクリーニング
            # Am2, G4 などの「コード名+数字」を「単音+数字」に置換
            processed_abc = re.sub(r'([A-G])m(\d)', r'\1\2', abc_text)
            
            # タイトル、キー、拍子の表記ゆれを修正
            processed_abc = processed_abc.replace("title=", "T:").replace("key=", "K:").replace("meter=", "M:")
            
            # 末尾に改行がないとパースに失敗することがあるため補完
            processed_abc = processed_abc.strip() + "\n\n"

            # 2. 一時ファイルを使用した解析（None エラー回避の決定打）
            with tempfile.NamedTemporaryFile(mode='w', suffix='.abc', delete=False, encoding='utf-8') as tmp:
                tmp.write(processed_abc)
                tmp_file_path = tmp.name

            # ファイルパスを渡すことで、music21 は確実に ABC 形式として認識する
            score = converter.parse(tmp_file_path, format='abc')

            if score is None:
                raise ValueError("music21 のファイル解析結果が None です。データ形式が不正です。")

            # 3. 楽譜構造の正規化
            # Scoreオブジェクトであることを保証
            if not isinstance(score, stream.Score):
                new_score = stream.Score()
                new_score.append(score)
                score = new_score

            # 小節構造を強制生成（これがないとMIDI書き出しでコケる原因になる）
            if not score.parts:
                score.makeMeasures(inPlace=True)
            else:
                for part in score.parts:
                    part.makeMeasures(inPlace=True)
            
            # 反復記号（|: :|）を実際の音符に展開（MIDI再生互換性のため）
            score = score.expandRepeats()

            logger.info(f"ABC記譜法の解析に成功しました。オブジェクト: {score}")
            return score
            
        except Exception as e:
            logger.error(f"ABC記譜法の解析に失敗しました: {e}")
            # 失敗した時のテキストを一部表示して原因特定を助ける
            logger.debug(f"解析対象テキスト(冒頭):\n{abc_text[:200]}")
            raise e
        
        finally:
            # 4. 後処理: 一時ファイルの確実な削除
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.remove(tmp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"一時ファイルの削除に失敗しました: {cleanup_error}")

    def _convert_abc_to_music21(self, abc_text: str):
        """
        ABC記譜法をmusic21のScoreオブジェクトに変換する内部メソッド。
        
        Args:
            abc_text: 変換対象のABC記譜法テキスト。
            
        Returns:
            music21.stream.Score: 変換された楽譜オブジェクト。
        """
        import music21
        
        # music21.converter.parse()を使用してABC記譜法を解析
        score = music21.converter.parse(abc_text)
        
        return score

    def extract_metadata(self, score) -> dict:
        """
        楽譜オブジェクトからメタデータを抽出します。
        
        Args:
            score: music21のScoreオブジェクト。
            
        Returns:
            dict: 抽出されたメタデータ。
        """
        metadata = {
            "title": None,
            "composer": None,
            "key": None,
            "time_signature": None,
        }
        
        # タイトルの抽出
        if score.metadata:
            metadata["title"] = score.metadata.title
            metadata["composer"] = score.metadata.composer
        
        # キーの取得
        key = score.analyze('key')
        metadata["key"] = key.name
        
        # 拍子の取得
        meter = score.timeSignature
        if meter:
            metadata["time_signature"] = f"{meter.numerator}/{meter.denominator}"
        
        return metadata