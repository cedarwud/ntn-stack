#!/usr/bin/env python3
"""
Claude API 直接調用腳本
使用 ANTHROPIC_BASE_URL 和 ANTHROPIC_AUTH_TOKEN
"""

import requests
import json
import os
import sys
import time
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sat/ntn-stack/claude_api_calls.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ClaudeAPIClient:
    def __init__(self):
        """初始化 Claude API 客戶端"""
        self.base_url = os.getenv('ANTHROPIC_BASE_URL')
        self.auth_token = os.getenv('ANTHROPIC_AUTH_TOKEN')
        
        if not self.base_url:
            raise ValueError("❌ 需要設定 ANTHROPIC_BASE_URL 環境變數")
        
        if not self.auth_token:
            raise ValueError("❌ 需要設定 ANTHROPIC_AUTH_TOKEN 環境變數")
        
        # 確保 URL 格式正確
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        self.endpoint = f"{self.base_url}v1/messages"
        
        logger.info(f"🔗 API 端點: {self.endpoint}")
        logger.info(f"🔑 Token 前綴: {self.auth_token[:10]}...")

    def call_claude(self, query, model="claude-sonnet-4-20250514", max_tokens=2000):
        """
        調用 Claude API
        
        Args:
            query (str): 要發送的查詢
            model (str): 使用的模型
            max_tokens (int): 最大回應 token 數
        
        Returns:
            dict: API 回應結果
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
        
        try:
            logger.info(f"🚀 發送查詢: {query[:100]}...")
            
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # 記錄回應狀態
            logger.info(f"📊 HTTP 狀態: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                claude_response = result.get('content', [{}])[0].get('text', '無回應內容')
                
                logger.info("✅ API 調用成功")
                logger.info(f"💬 Claude 回應: {claude_response[:200]}...")
                
                return {
                    'success': True,
                    'response': claude_response,
                    'full_result': result
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ API 調用失敗: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            error_msg = "請求超時"
            logger.error(f"⏰ {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except requests.exceptions.ConnectionError:
            error_msg = f"連接錯誤，無法連接到 {self.base_url}"
            logger.error(f"🔌 {error_msg}")
            return {'success': False, 'error': error_msg}
            
        except Exception as e:
            error_msg = f"未知錯誤: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return {'success': False, 'error': error_msg}

def main():
    """主函數"""
    # 從命令列參數獲取查詢，或使用預設
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = "what time is it now"
    
    logger.info("=" * 60)
    logger.info("🤖 Claude API 調用開始")
    logger.info(f"📝 查詢內容: {query}")
    
    try:
        # 建立 API 客戶端
        client = ClaudeAPIClient()
        
        # 調用 API
        result = client.call_claude(query)
        
        if result['success']:
            print(f"\n🎉 Claude 回應:\n{result['response']}\n")
            logger.info("✅ 調用完成")
            return 0
        else:
            print(f"\n❌ 調用失敗: {result['error']}\n")
            logger.error("❌ 調用失敗")
            return 1
            
    except Exception as e:
        error_msg = f"初始化失敗: {str(e)}"
        logger.error(f"💥 {error_msg}")
        print(f"\n❌ {error_msg}\n")
        return 1
    
    finally:
        logger.info("=" * 60)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)