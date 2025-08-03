#!/usr/bin/env python3
"""
Claude API 智能重試系統
失敗時自動設定下一次重試時間（+1小時），直到成功收到 "OK" 回應
"""

import requests
import json
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sat/ntn-stack/claude-auto-query/claude_retry.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ClaudeRetrySystem:
    def __init__(self):
        """初始化重試系統"""
        self.base_url = os.getenv('ANTHROPIC_BASE_URL')
        self.auth_token = os.getenv('ANTHROPIC_AUTH_TOKEN')
        self.retry_state_file = '/home/sat/ntn-stack/claude-auto-query/retry_state.json'
        self.cron_backup_file = '/home/sat/ntn-stack/claude-auto-query/original_cron.backup'
        self.success_log_file = '/home/sat/ntn-stack/logs/cron.log'
        
        if not self.base_url or not self.auth_token:
            raise ValueError("❌ 需要設定 ANTHROPIC_BASE_URL 和 ANTHROPIC_AUTH_TOKEN 環境變數")
        
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        self.endpoint = f"{self.base_url}v1/messages"
        logger.info(f"🔗 API 端點: {self.endpoint}")

    def load_retry_state(self):
        """載入重試狀態"""
        try:
            if os.path.exists(self.retry_state_file):
                with open(self.retry_state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"📋 載入重試狀態: {state}")
                    return state
        except Exception as e:
            logger.warning(f"⚠️  無法載入重試狀態: {e}")
        
        return {"retry_count": 0, "last_failure": None, "original_query": None}

    def save_retry_state(self, state):
        """保存重試狀態"""
        try:
            with open(self.retry_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"💾 保存重試狀態: {state}")
        except Exception as e:
            logger.error(f"❌ 無法保存重試狀態: {e}")

    def call_claude_api(self, query):
        """調用 Claude API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
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
            
            logger.info(f"📊 HTTP 狀態: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                claude_response = result.get('content', [{}])[0].get('text', '').strip()
                
                logger.info(f"💬 Claude 回應: {claude_response[:200]}...")
                
                return {
                    'success': True,
                    'response': claude_response,
                    'is_ok_response': claude_response.upper() == 'OK'
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ API 調用失敗: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f"請求異常: {str(e)}"
            logger.error(f"💥 {error_msg}")
            return {'success': False, 'error': error_msg}

    def schedule_retry(self, query, retry_count):
        """設定重試任務 - 在當前時間 + retry_count 小時後執行"""
        try:
            # 計算下次執行時間
            next_run = datetime.now() + timedelta(hours=retry_count)
            
            # 格式化為 cron 時間
            cron_minute = next_run.minute
            cron_hour = next_run.hour
            cron_day = next_run.day
            cron_month = next_run.month
            
            # 構建 cron 表達式 (特定時間執行一次)
            cron_expr = f"{cron_minute} {cron_hour} {cron_day} {cron_month} *"
            
            logger.info(f"⏰ 設定重試任務: {next_run.strftime('%Y-%m-%d %H:%M')}")
            logger.info(f"📅 Cron 表達式: {cron_expr}")
            
            # 備份當前 crontab (如果還沒備份過)
            if not os.path.exists(self.cron_backup_file):
                try:
                    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                    if result.returncode == 0:
                        with open(self.cron_backup_file, 'w') as f:
                            f.write(result.stdout)
                        logger.info("💾 已備份原始 crontab")
                except Exception as e:
                    logger.warning(f"⚠️  無法備份 crontab: {e}")
            
            # 獲取當前 crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # 移除舊的重試任務
            lines = [line for line in current_crontab.split('\n') 
                    if 'claude_retry_system.py' not in line and line.strip()]
            
            # 構建環境變數
            env_vars = f"ANTHROPIC_BASE_URL='{self.base_url}' ANTHROPIC_AUTH_TOKEN='{self.auth_token}'"
            
            # 添加新的重試任務
            retry_cmd = f"{cron_expr} cd /home/sat/ntn-stack/claude-auto-query && {env_vars} python3 claude_retry_system.py '{query}' >> claude_retry.log 2>&1"
            lines.append(retry_cmd)
            
            # 更新 crontab
            new_crontab = '\n'.join(lines) + '\n'
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                logger.info(f"✅ 重試任務已設定，將在 {retry_count} 小時後執行")
                return True
            else:
                logger.error("❌ 設定重試任務失敗")
                return False
                
        except Exception as e:
            logger.error(f"💥 設定重試任務異常: {e}")
            return False

    def clear_retry_tasks(self):
        """清除所有相關任務 (包括原始一次性任務和重試任務)"""
        try:
            # 獲取當前 crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return
            
            # 移除所有 Claude 相關任務 (包括 claude_retry_system.py 和 claude_auto_query.sh)
            lines = [line for line in result.stdout.split('\n') 
                    if not any(script in line for script in [
                        'claude_retry_system.py',
                        'claude_auto_query.sh',
                        'claude-auto-query'
                    ]) and line.strip()]
            
            # 更新 crontab
            new_crontab = '\n'.join(lines) + '\n'
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                logger.info("🧹 已清除所有 Claude 相關任務 (包括原始任務和重試任務)")
            
        except Exception as e:
            logger.error(f"❌ 清除任務失敗: {e}")

    def log_success_time(self, query, retry_count):
        """記錄成功時間到 cron.log"""
        try:
            # 確保 logs 目錄存在
            os.makedirs(os.path.dirname(self.success_log_file), exist_ok=True)
            
            success_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 構建日誌訊息
            if retry_count == 0:
                log_message = f"[{success_time}] ✅ Claude 查詢成功 (首次) - 查詢: \"{query[:100]}{'...' if len(query) > 100 else ''}\""
            else:
                log_message = f"[{success_time}] ✅ Claude 查詢成功 (重試 {retry_count} 次後) - 查詢: \"{query[:100]}{'...' if len(query) > 100 else ''}\""
            
            # 寫入成功日誌
            with open(self.success_log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
            
            logger.info(f"📝 成功時間已記錄到: {self.success_log_file}")
            
        except Exception as e:
            logger.error(f"❌ 記錄成功時間失敗: {e}")

    def run_query_with_retry(self, query):
        """執行查詢並處理重試邏輯"""
        logger.info("=" * 60)
        logger.info("🤖 Claude 智能重試系統啟動")
        logger.info(f"📝 查詢內容: {query}")
        
        # 載入重試狀態
        state = self.load_retry_state()
        
        # 如果是新查詢，重置狀態
        if state.get('original_query') != query:
            state = {"retry_count": 0, "last_failure": None, "original_query": query}
        
        current_retry = state['retry_count']
        logger.info(f"🔄 當前重試次數: {current_retry}")
        
        # 調用 API
        result = self.call_claude_api(query)
        
        if result['success']:
            if result.get('is_ok_response'):
                logger.info("🎉 收到 'OK' 回應！任務成功完成")
                
                # 記錄成功時間
                self.log_success_time(query, current_retry)
                
                # 清除重試狀態和任務
                self.clear_retry_tasks()
                if os.path.exists(self.retry_state_file):
                    os.remove(self.retry_state_file)
                
                logger.info("✅ 重試系統已重置")
                return True
            else:
                logger.warning("⚠️  API 調用成功但未收到 'OK' 回應")
                logger.info(f"📝 實際回應: {result.get('response', '')[:500]}")
                
                # 更新重試狀態
                state['retry_count'] = current_retry + 1
                state['last_failure'] = datetime.now().isoformat()
                self.save_retry_state(state)
                
                # 設定下次重試
                if self.schedule_retry(query, state['retry_count']):
                    logger.info(f"⏳ 已設定 {state['retry_count']} 小時後重試")
                    return False
        else:
            logger.error(f"❌ API 調用失敗: {result.get('error', '未知錯誤')}")
            
            # 更新重試狀態
            state['retry_count'] = current_retry + 1
            state['last_failure'] = datetime.now().isoformat()
            self.save_retry_state(state)
            
            # 設定下次重試
            if self.schedule_retry(query, state['retry_count']):
                logger.info(f"⏳ 已設定 {state['retry_count']} 小時後重試")
                return False
        
        logger.error("💥 重試設定失敗")
        return False

def main():
    """主函數"""
    # 使用預設查詢，確保 Claude 會回應 "OK"
    default_query = "Please respond with exactly 'OK' and nothing else."
    
    if len(sys.argv) >= 2:
        # 如果有提供參數，使用參數作為查詢
        query = ' '.join(sys.argv[1:])
        logger.info(f"🔧 使用自訂查詢: {query}")
    else:
        # 如果沒有參數，使用預設查詢
        query = default_query
        logger.info(f"🤖 使用預設查詢: {query}")
    
    try:
        retry_system = ClaudeRetrySystem()
        success = retry_system.run_query_with_retry(query)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"💥 系統異常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()