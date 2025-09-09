def process(self) -> Dict[str, Any]:
        """執行完整的篩選流程 - v5.0 統一格式版本 + Phase 3 驗證框架"""
        logger.info("🚀 開始修復版增強智能衛星篩選處理 + Phase 3 驗證框架")
        logger.info("=" * 60)
        
        # 清理舊驗證快照 (確保生成最新驗證快照)
        if self.snapshot_file.exists():
            logger.info(f"🗑️ 清理舊驗證快照: {self.snapshot_file}")
            self.snapshot_file.unlink()
        
        # 載入軌道數據
        orbital_data = self.load_orbital_calculation_output()
        
        # 🎯 v5.0 統一格式：從 constellations 結構提取衛星數據
        all_satellites = []
        
        if 'constellations' in orbital_data:
            # 🎯 統一格式：處理 constellations 結構
            for constellation_name, constellation_data in orbital_data.get('constellations', {}).items():
                satellites = constellation_data.get('satellites', [])
                
                for sat_data in satellites:
                    # 確保每顆衛星都有 constellation 字段
                    sat_data['constellation'] = constellation_name
                    
                    # 確保有 satellite_id 字段
                    if 'satellite_id' not in sat_data:
                        sat_data['satellite_id'] = sat_data.get('name', f"{constellation_name}_unknown")
                    
                    all_satellites.append(sat_data)
                    
        elif 'satellites' in orbital_data:
            # 🔧 回退兼容：處理舊的 satellites 陣列格式
            satellites_list = orbital_data.get('satellites', [])
            
            for sat_data in satellites_list:
                # 保持原有的constellation字段，不覆寫
                if 'constellation' not in sat_data:
                    sat_data['constellation'] = 'unknown'
                all_satellites.append(sat_data)
        else:
            logger.error("❌ 數據格式錯誤：缺少 constellations 或 satellites 字段")
            return {
                'metadata': {'total_satellites': 0, 'processing_complete': False, 'error': 'invalid_data_format'},
                'satellites': []
            }
                
        logger.info(f"📊 開始處理 {len(all_satellites)} 顆衛星")
        
        if len(all_satellites) == 0:
            logger.error("❌ 沒有衛星數據可供處理")
            return {
                'metadata': {'total_satellites': 0, 'processing_complete': False, 'error': 'no_satellites_data'},
                'satellites': []
            }
        
        # 🛡️ Phase 3 新增：預處理驗證
        validation_context = {
            'stage_name': 'stage2_satellite_visibility_filter',
            'processing_start': datetime.now(timezone.utc).isoformat(),
            'input_satellites_count': len(all_satellites),
            'observer_coordinates': {
                'latitude': self.observer_lat,
                'longitude': self.observer_lon,
                'altitude': self.observer_alt
            },
            'filtering_criteria': self.filtering_criteria
        }
        
        if self.validation_enabled and self.validation_adapter:
            try:
                logger.info("🔍 執行預處理驗證 (軌道數據結構檢查)...")
                
                # 執行預處理驗證
                import asyncio
                pre_validation_result = asyncio.run(
                    self.validation_adapter.pre_process_validation(all_satellites, validation_context)
                )
                
                if not pre_validation_result.get('success', False):
                    error_msg = f"預處理驗證失敗: {pre_validation_result.get('blocking_errors', [])}"
                    logger.error(f"🚨 {error_msg}")
                    raise ValueError(f"Phase 3 Validation Failed: {error_msg}")
                
                logger.info("✅ 預處理驗證通過，繼續可見性篩選...")
                
            except Exception as e:
                logger.error(f"🚨 Phase 3 預處理驗證異常: {str(e)}")
                if "Phase 3 Validation Failed" in str(e):
                    raise  # 重新拋出驗證失敗錯誤
                else:
                    logger.warning("   使用舊版驗證邏輯繼續處理")
        
        # 階段 0: 可見性預篩選
        visible_satellites = self._visibility_prefilter(all_satellites)
        
        # 簡化篩選（避免過度篩選）
        filtered_satellites = self._simple_filtering(visible_satellites)
        
        # 防止除零錯誤
        if len(all_satellites) == 0:
            retention_rate = 0.0
        else:
            retention_rate = (1 - len(filtered_satellites)/len(all_satellites))*100
        
        # 準備處理指標
        processing_metrics = {
            'input_satellites': len(all_satellites),
            'visible_satellites': len(visible_satellites),
            'filtered_satellites': len(filtered_satellites),
            'retention_rate': retention_rate,
            'processing_time': datetime.now(timezone.utc).isoformat(),
            'filtering_criteria_applied': self.filtering_criteria
        }
        
        # 🛡️ Phase 3 新增：後處理驗證
        if self.validation_enabled and self.validation_adapter:
            try:
                logger.info("🔍 執行後處理驗證 (可見性篩選結果檢查)...")
                
                # 執行後處理驗證
                post_validation_result = asyncio.run(
                    self.validation_adapter.post_process_validation(filtered_satellites, processing_metrics)
                )
                
                # 檢查驗證結果
                if not post_validation_result.get('success', False):
                    error_msg = f"後處理驗證失敗: {post_validation_result.get('error', '未知錯誤')}"
                    logger.error(f"🚨 {error_msg}")
                    
                    # 檢查是否為品質門禁阻斷
                    if 'Quality gate blocked' in post_validation_result.get('error', ''):
                        raise ValueError(f"Phase 3 Quality Gate Blocked: {error_msg}")
                    else:
                        logger.warning("   後處理驗證失敗，但繼續處理 (降級模式)")
                else:
                    logger.info("✅ 後處理驗證通過，可見性篩選結果符合學術標準")
                    
                    # 記錄驗證摘要
                    academic_compliance = post_validation_result.get('academic_compliance', {})
                    if academic_compliance.get('compliant', False):
                        logger.info(f"🎓 學術合規性: Grade {academic_compliance.get('grade_level', 'Unknown')}")
                    else:
                        logger.warning(f"⚠️ 學術合規性問題: {len(academic_compliance.get('violations', []))} 項違規")
                
                # 將驗證結果加入處理指標
                processing_metrics['validation_summary'] = post_validation_result
                
            except Exception as e:
                logger.error(f"🚨 Phase 3 後處理驗證異常: {str(e)}")
                if "Phase 3 Quality Gate Blocked" in str(e):
                    raise  # 重新拋出品質門禁阻斷錯誤
                else:
                    logger.warning("   使用舊版驗證邏輯繼續處理")
                    processing_metrics['validation_summary'] = {
                        'success': False,
                        'error': str(e),
                        'fallback_used': True
                    }
        
        # 保存結果
        output_file = self.save_filtered_output(filtered_satellites, len(all_satellites))
        
        # 輸出統計
        logger.info("=" * 60)
        logger.info("✅ 修復版增強智能篩選完成")
        logger.info(f"  輸入: {len(all_satellites)} 顆")
        logger.info(f"  輸出: {len(filtered_satellites)} 顆")
        if len(all_satellites) > 0:
            logger.info(f"  篩選率: {retention_rate:.1f}%")
        
        # 構建返回結果
        result = {
            'metadata': {
                'total_satellites': len(filtered_satellites),
                'input_satellites': len(all_satellites),
                'processing_complete': True,
                'data_format_version': 'unified_v1.1_phase3',
                'validation_summary': processing_metrics.get('validation_summary', None),
                'academic_compliance': {
                    'phase3_validation': 'enabled' if self.validation_enabled else 'disabled',
                    'processing_metrics': processing_metrics
                }
            },
            'satellites': filtered_satellites
        }
        
        # 🔍 自動保存驗證快照
        snapshot_saved = self.save_validation_snapshot(result)
        if snapshot_saved:
            logger.info(f"📊 驗證快照已自動保存: {self.snapshot_file}")
        else:
            logger.warning("⚠️ 驗證快照自動保存失敗")
        
        return result