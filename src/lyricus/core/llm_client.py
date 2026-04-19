import json
import re
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from loguru import logger

from lyricus.utils.env import settings
from lyricus.utils.utils import sanitize_error_message
from lyricus.core.sys_prompt import ABC_GENERATION_SYSTEM_PROMPT


class LLMClient:
    """
    Ollama APIを使用してLLMと通信するクラス。
    ABC記譜法の生成や、テキストの解析を行います。
    """

    def __init__(self, model: Optional[str] = None):
        """
        LLMクライアントを初期化します。
        
        Args:
            model: 使用するモデル名。指定がない場合はenv.pyの設定を使用します。
        """
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        
        # LangChainのChatOllamaを使用してクライアントを初期化
        self.client = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.7,
        )
        
        logger.info(f"LLMクライアントを初期化しました。Model: {self.model}, URL: {self.base_url}")

    def generate_abc_notation(self, prompt: str) -> str:
        """
        ストリーミングを使用してABC記譜法を生成します。
        エラーや中断が発生した場合、即座に接続を切りOllama側の計算を停止させます。
        """
        full_response = []
        messages = [
            SystemMessage(content=ABC_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=f"テーマ：{prompt}")
        ]

        try:
            logger.info(f"生成を開始します (Stream Mode): {self.model}")
            
            # streamメソッドにより、少しずつデータを受け取る
            for chunk in self.client.stream(messages):
                content = chunk.content
                full_response.append(content)
                
                # --- 動的なバリデーション ---
                # 例えば、最初の100文字で 'X:1' が現れなかったら、
                # お喋りモード（失敗）とみなして即座に中断する
                current_text = "".join(full_response)
                if len(current_text) > 100 and "X:" not in current_text:
                    logger.error("LLMがABC記譜法以外の出力を開始したため、接続を強制終了します。")
                    break # ここでループを抜けると、Ollamaへの接続が切れる
            
            abc_text = "".join(full_response).strip()
            abc_block = self._extract_abc_block(abc_text)
            
            if not abc_block:
                raise RuntimeError("有効なABC記譜法を抽出できませんでした。")
                
            return abc_block

        except Exception as e:
            # このブロックに入った時点で、ストリーミングのイテレータは破棄され、
            # HTTPコネクションが切断されるため、Ollama側のプロセスも停止しやすい。
            logger.error(f"Ollamaとの通信中にエラーまたは中断が発生しました: {e}")
            raise RuntimeError(f"生成プロセスをクリーンに停止しました: {e}")
    
    def _extract_abc_block(self, text: str) -> Optional[str]:
        """
        テキストからABC記譜法のブロックを抽出します。
        X:1から始まるブロックを正規表現で検索します。
        
        Args:
            text: 検索対象のテキスト。
            
        Returns:
            Optional[str]: 抽出されたABCブロック。見つからない場合はNone。
        """
        # X:1から始まるABCブロックを検索する正規表現
        # 改行や空白を含むブロックをキャプチャ
        pattern = r'X:\d+.*?(?=\nX:\d+|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            # 最初のマッチを返す
            return matches[0].strip()
        
        return None

    def parse_music_theory(self, abc_text: str) -> dict:
        """
        ABC記譜法から音楽理論の情報を解析します。
        （現在は簡易的な実装。将来的に詳細な解析を追加します。）
        
        Args:
            abc_text: 解析対象のABC記譜法テキスト。
            
        Returns:
            dict: 解析結果を含む辞書。
        """
        # 簡易的な解析：キーと拍子を抽出
        result = {
            "key": None,
            "time_signature": None,
            "notes_count": 0,
        }
        
        # キーの抽出（K:）
        key_match = re.search(r'K:\s*([A-G][#b]?m?)', abc_text)
        if key_match:
            result["key"] = key_match.group(1)
        
        # 拍子の抽出（L:やM:）
        time_match = re.search(r'(?:L:|M:)\s*(\d+/\d+)', abc_text)
        if time_match:
            result["time_signature"] = time_match.group(1)
        
        # 音符の数をカウント
        note_pattern = r'[A-G][#b]?[0-9]*'
        notes = re.findall(note_pattern, abc_text)
        result["notes_count"] = len(notes)
        
        return result
    
    def _make_request(self, prompt: str, system_prompt: str) -> str:
        """
        Ollama API にリクエストを送信します。
        
        Args:
            prompt: ユーザーの指示文。
            system_prompt: システムプロンプト。
            
        Returns:
            str: LLM の応答。
            
        Raises:
            RuntimeError: API 呼び出しに失敗した場合。
        """
        try:
            import requests
            from requests.exceptions import RequestException
            
            # API リクエストの構築
            url = f"{self.base_url}/api/generate"
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
            }
            
            # リクエストを送信
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            
            # レスポンスの検証
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except RequestException as e:
            # 接続エラーやタイムアウトなどの例外
            logger.error(f"Ollama API への接続に失敗しました: {sanitize_error_message(e)}")
            raise RuntimeError("Ollama API に接続できません。ネットワーク接続を確認してください。")
            
        except ValueError as e:
            # JSON パースエラー
            logger.error(f"API レスポンスの解析に失敗しました: {sanitize_error_message(e)}")
            raise RuntimeError("Ollama API から有効なレスポンスが返されませんでした。")
            
        except Exception as e:
            # その他の例外
            logger.error(f"LLM API 呼び出しに失敗しました: {sanitize_error_message(e)}")
            raise RuntimeError("LLM API 呼び出しに予期せぬエラーが発生しました。")