from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger


class BaseMetric(ABC):
    """
    評価メトリクスの基盤クラス。
    
    音楽理論に基づく評価指標を実装するための抽象基底クラスです。
    各メトリクスは `BaseMetric` を継承して実装します。
    """

    def __init__(self, name: str, description: str):
        """
        評価メトリクスを初期化します。
        
        Args:
            name: メトリクスの名前。
            description: メトリクスの説明。
        """
        self.name = name
        self.description = description
        
        logger.info(f"メトリクス '{name}' を初期化しました。")

    @abstractmethod
    def calculate(self, score) -> dict:
        """
        楽譜オブジェクトから評価値を計算します。
        
        Args:
            score: music21 の Score オブジェクト。
            
        Returns:
            dict: 評価結果を含む辞書。
                - "value": 評価値
                - "unit": 単位（例：%, 1/100 など）
                - "description": 評価の説明
        """
        pass

    def get_result(self, score) -> dict:
        """
        楽譜オブジェクトから評価結果を取得します。
        
        Args:
            score: music21 の Score オブジェクト。
            
        Returns:
            dict: 評価結果を含む辞書。
        """
        result = self.calculate(score)
        logger.debug(f"メトリクス '{self.name}' の計算結果: {result}")
        return result


class CompositeMetric:
    """
    複数のメトリクスを組み合わせるコンポジットメトリクス。
    
    複数の評価メトリクスを組み合わせ、総合評価を行うクラスです。
    """

    def __init__(self, metrics: list[BaseMetric]):
        """
        コンポジットメトリクスを初期化します。
        
        Args:
            metrics: 使用するメトリクスのリスト。
        """
        self.metrics = metrics
        self.name = "CompositeMetric"
        self.description = "複数のメトリクスを組み合わせた総合評価"
        
        logger.info(f"コンポジットメトリクスを初期化しました。メトリクス数: {len(metrics)}")

    def calculate(self, score) -> dict:
        """
        全てのメトリクスを計算し、総合評価を返します。
        
        Args:
            score: music21 の Score オブジェクト。
            
        Returns:
            dict: 総合評価結果を含む辞書。
        """
        results = {}
        total_score = 0
        max_score = 0
        
        for metric in self.metrics:
            result = metric.get_result(score)
            results[metric.name] = result
            
            # 評価値の合計と最大値を計算
            value = result.get("value", 0)
            unit = result.get("unit", "")
            
            if unit == "%":
                total_score += value
                max_score += 100
            else:
                total_score += value
                max_score += 100
        
        # 総合評価の計算
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        results["overall_score"] = {
            "value": overall_score,
            "unit": "%",
            "description": "総合評価スコア"
        }
        
        logger.info(f"総合評価を計算しました。スコア: {overall_score:.2f}%")
        return results