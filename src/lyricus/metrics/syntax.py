import re
from typing import Optional

from loguru import logger

from lyricus.metrics.base import BaseMetric


class ABCSyntaxMetric(BaseMetric):
    """
    ABC 記譜法の文法チェックメトリクス。
    
    ABC 記譜法の基本的な文法ルールをチェックし、
    文法エラーの有無や、X:1 から始まるブロックの有無を検出します。
    """

    def __init__(self):
        """
        ABC 文法チェックメトリクスを初期化します。
        """
        super().__init__(
            name="ABCSyntaxMetric",
            description="ABC 記譜法の文法ルールをチェックするメトリクス"
        )
        
        # ABC 記譜法の必須フィールドの正規表現パターン
        self.required_fields = {
            "X:": r'X:\d+',
            "K:": r'K:\s*[A-G][#b]?m?',
            "M:|L:": r'(?:M:|L:)\s*\d+/\d+',
        }

    def calculate(self, score) -> dict:
        """
        ABC 記譜法の文法をチェックします。
        
        Args:
            score: music21 の Score オブジェクト。
            
        Returns:
            dict: 文法チェック結果。
        """
        # ABC テキストの取得
        abc_text = self._extract_abc_text(score)
        
        if not abc_text:
            return {
                "value": 0,
                "unit": "%",
                "description": "ABC テキストが取得できませんでした"
            }
        
        # 文法チェックの実行
        checks = {
            "has_x_block": self._check_x_block(abc_text),
            "has_key": self._check_key(abc_text),
            "has_time_signature": self._check_time_signature(abc_text),
            "has_title": self._check_title(abc_text),
        }
        
        # 評価スコアの計算
        score_value = self._calculate_score(checks)
        
        return {
            "value": score_value,
            "unit": "%",
            "description": f"文法チェック完了。スコア: {score_value:.2f}%"
        }

    def _extract_abc_text(self, score) -> Optional[str]:
        """
        Score オブジェクトから ABC テキストを抽出します。
        
        Args:
            score: music21 の Score オブジェクト。
            
        Returns:
            Optional[str]: ABC テキスト。見つからない場合は None。
        """
        try:
            # music21 の converter を使用して ABC テキストを取得
            from music21.converter import abc
            return abc(score)
        except Exception as e:
            logger.error(f"ABC テキストの抽出に失敗しました: {e}")
            return None

    def _check_x_block(self, abc_text: str) -> bool:
        """
        X:1 から始まるブロックが存在するかチェックします。
        
        Args:
            abc_text: ABC 記譜法テキスト。
            
        Returns:
            bool: X:1 ブロックが存在する場合は True。
        """
        pattern = r'X:\d+'
        return bool(re.search(pattern, abc_text))

    def _check_key(self, abc_text: str) -> bool:
        """
        キー指定（K:）が存在するかチェックします。
        
        Args:
            abc_text: ABC 記譜法テキスト。
            
        Returns:
            bool: キー指定が存在する場合は True。
        """
        pattern = r'K:\s*[A-G][#b]?m?'
        return bool(re.search(pattern, abc_text))

    def _check_time_signature(self, abc_text: str) -> bool:
        """
        拍子指定（M: または L:）が存在するかチェックします。
        
        Args:
            abc_text: ABC 記譜法テキスト。
            
        Returns:
            bool: 拍子指定が存在する場合は True。
        """
        pattern = r'(?:M:|L:)\s*\d+/\d+'
        return bool(re.search(pattern, abc_text))

    def _check_title(self, abc_text: str) -> bool:
        """
        タイトル指定（T:）が存在するかチェックします。
        
        Args:
            abc_text: ABC 記譜法テキスト。
            
        Returns:
            bool: タイトル指定が存在する場合は True。
        """
        pattern = r'T:'
        return bool(re.search(pattern, abc_text))

    def _calculate_score(self, checks: dict) -> float:
        """
        チェック結果から評価スコアを計算します。
        
        Args:
            checks: チェック結果の辞書。
            
        Returns:
            float: 評価スコア（0-100）。
        """
        # 必須項目の重み付け
        weights = {
            "has_x_block": 0.3,  # X:1 ブロックは必須
            "has_key": 0.2,      # キー指定は推奨
            "has_time_signature": 0.2,  # 拍子指定は推奨
            "has_title": 0.3,    # タイトルは推奨
        }
        
        # スコアの計算
        score = 0.0
        for field, check_result in checks.items():
            weight = weights.get(field, 0.0)
            if check_result:
                score += weight * 100
        
        return score


class ABCStructureMetric(BaseMetric):
    """
    ABC 記譜法の構造チェックメトリクス。
    
    楽譜の構造（音符の配置、小節の区切りなど）をチェックします。
    """

    def __init__(self):
        """
        ABC 構造チェックメトリクスを初期化します。
        """
        super().__init__(
            name="ABCStructureMetric",
            description="ABC 記譜法の構造をチェックするメトリクス"
        )

    def calculate(self, score) -> dict:
        """
        ABC 記譜法の構造をチェックします。
        
        Args:
            score: music21 の Score オブジェクト。
            
        Returns:
            dict: 構造チェック結果。
        """
        abc_text = self._extract_abc_text(score)
        
        if not abc_text:
            return {
                "value": 0,
                "unit": "%",
                "description": "ABC テキストが取得できませんでした"
            }
        
        # 構造チェックの実行
        checks = {
            "has_measures": self._check_measures(abc_text),
            "has_rests": self._check_rests(abc_text),
            "has_chords": self._check_chords(abc_text),
        }
        
        # 評価スコアの計算
        score_value = self._calculate_score(checks)
        
        return {
            "value": score_value,
            "unit": "%",
            "description": f"構造チェック完了。スコア: {score_value:.2f}%"
        }

    def _check_measures(self, abc_text: str) -> bool:
        """
        小節区切り（|）が存在するかチェックします。
        
        Args:
            abc_text: ABC 記譜法テキスト。
            
        Returns:
            bool: 小節区切りが存在する場合は True。
        """
        return "|" in abc_text

    def _check_rests(self, abc_text: str) -> bool:
        """
        休符（z）が含まれているかチェックします。
        
        Args:
            abc_text: ABC 記譜法テキスト。
            
        Returns:
            bool: 休符が含まれている場合は True。
        """
        return bool(re.search(r'z\d*', abc_text))

    def _check_chords(self, abc_text: str) -> bool:
        """
        和音（複数の音符が並んでいる）が含まれているかチェックします。
        
        Args:
            abc_text: ABC 記譜法テキスト。
            
        Returns:
            bool: 和音が含まれている場合は True。
        """
        # 連続する音符パターンを検索
        chord_pattern = r'[A-G][#b]?[0-9]*[A-G][#b]?[0-9]*'
        matches = re.findall(chord_pattern, abc_text)
        return len(matches) > 1

    def _calculate_score(self, checks: dict) -> float:
        """
        チェック結果から評価スコアを計算します。
        
        Args:
            checks: チェック結果の辞書。
            
        Returns:
            float: 評価スコア（0-100）。
        """
        # 構造チェックの重み付け
        weights = {
            "has_measures": 0.4,
            "has_rests": 0.2,
            "has_chords": 0.4,
        }
        
        score = 0.0
        for field, check_result in checks.items():
            weight = weights.get(field, 0.0)
            if check_result:
                score += weight * 100
        
        return score