#!/usr/bin/env python3
"""
Stage 3 執行腳本
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加路徑
sys.path.append("/orbit-engine/src")
from stages.stage3_signal_analysis.stage3_main_processor import Stage3MainProcessor

def main():
    print(f"[{datetime.now().isoformat()}] Loading and transforming Stage 2 outputs...")

    try:
        # 載入Stage 2的輸出數據
        with open("/orbit-engine/data/outputs/stage2/stage2_complete_aggregation_output.json", "r") as f:
            stage2_data = json.load(f)

        # 轉換數據格式：visible_satellites -> filtered_satellites
        transformed_data = {
            "filtered_satellites": []
        }

        for sat_id, sat_data in stage2_data["visible_satellites"].items():
            satellite_entry = {
                "satellite_id": sat_id,
                "satellite_name": sat_data.get("satellite_name", f"SAT_{sat_id}"),
                "constellation": sat_data.get("constellation", "unknown"),
                "orbital_data": sat_data.get("complete_orbital_data", {}),
                "tle_data": sat_data.get("tle_data", {}),
                "visibility_status": "visible"
            }
            transformed_data["filtered_satellites"].append(satellite_entry)

        num_satellites = len(transformed_data["filtered_satellites"])
        print(f"[{datetime.now().isoformat()}] Transformed data for {num_satellites} satellites")

        print(f"[{datetime.now().isoformat()}] Initializing Stage 3 Main Processor...")
        processor = Stage3MainProcessor()

        print(f"[{datetime.now().isoformat()}] Executing Stage 3 with transformed input...")
        results = processor.execute(input_data=transformed_data)

        print(f"[{datetime.now().isoformat()}] Stage 3 execution completed successfully")
        print("Results summary:")
        if "signal_quality_data" in results:
            print(f"Signal quality calculated for {len(results['signal_quality_data'])} satellites")

        # 輸出處理摘要
        if "processing_summary" in results:
            print(json.dumps(results["processing_summary"], indent=2, default=str))

        return results

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error in Stage 3: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()