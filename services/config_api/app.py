#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import json
import logging
import subprocess
import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("config-api")

# 常量定義
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "config"))
UERANSIM_CONFIG_DIR = os.path.join(CONFIG_DIR, "ueransim")
GENERATED_CONFIG_DIR = os.path.join(CONFIG_DIR, "generated")
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts"))

# 確保目錄存在
os.makedirs(GENERATED_CONFIG_DIR, exist_ok=True)
os.makedirs(UERANSIM_CONFIG_DIR, exist_ok=True)

# 記錄當前配置路徑
logger.info(f"配置目錄: {CONFIG_DIR}")
logger.info(f"UERANSIM配置目錄: {UERANSIM_CONFIG_DIR}")
logger.info(f"生成配置目錄: {GENERATED_CONFIG_DIR}")
logger.info(f"腳本目錄: {SCRIPTS_DIR}")


# 模型定義
class ConfigTemplate(BaseModel):
    name: str
    description: str
    path: str


class ConfigParameter(BaseModel):
    name: str
    description: str
    value: str
    default: str
    type: str = "string"


class ConfigResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None


class ApplyConfigRequest(BaseModel):
    gnb_config: Optional[str] = None
    ue_config: Optional[str] = None
    container: Optional[str] = None


# 創建FastAPI應用
app = FastAPI(
    title="UERANSIM 配置API",
    description="用於管理UERANSIM的gNodeB和UE配置",
    version="1.0.0",
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 工具函數
def get_config_templates() -> List[ConfigTemplate]:
    """獲取所有可用的配置模板"""
    templates = []

    if not os.path.exists(UERANSIM_CONFIG_DIR):
        return templates

    for filename in os.listdir(UERANSIM_CONFIG_DIR):
        if filename.endswith(".yaml"):
            path = os.path.join(UERANSIM_CONFIG_DIR, filename)
            templates.append(
                ConfigTemplate(
                    name=filename.replace(".yaml", ""),
                    description=f"配置模板 {filename}",
                    path=path,
                )
            )

    return templates


def get_generated_configs() -> List[ConfigTemplate]:
    """獲取所有生成的配置文件"""
    configs = []

    if not os.path.exists(GENERATED_CONFIG_DIR):
        return configs

    for filename in os.listdir(GENERATED_CONFIG_DIR):
        if filename.endswith(".yaml"):
            path = os.path.join(GENERATED_CONFIG_DIR, filename)
            configs.append(
                ConfigTemplate(
                    name=filename.replace(".yaml", ""),
                    description=f"生成的配置 {filename}",
                    path=path,
                )
            )

    return configs


def generate_config(template_path: str, parameters: Dict, output_path: str) -> str:
    """根據模板和參數生成配置文件"""
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    try:
        # 讀取模板
        with open(template_path, "r") as f:
            template = yaml.safe_load(f)

        # 應用參數
        for key, value in parameters.items():
            if "." in key:
                # 處理嵌套參數 (例如 "amf.host")
                parts = key.split(".")
                current = template
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                # 簡單參數
                template[key] = value

        # 寫入生成的配置
        with open(output_path, "w") as f:
            yaml.dump(template, f, default_flow_style=False)

        return output_path

    except Exception as e:
        logger.error(f"生成配置時發生錯誤: {str(e)}")
        raise


def apply_config(
    gnb_config: Optional[str] = None,
    ue_config: Optional[str] = None,
    container: Optional[str] = None,
) -> Dict:
    """應用配置到UERANSIM容器"""
    script_path = os.path.join(SCRIPTS_DIR, "apply_config.sh")

    if not os.path.exists(script_path):
        raise FileNotFoundError(f"應用配置腳本不存在: {script_path}")

    cmd = [script_path]

    if gnb_config:
        cmd.extend(["-g", gnb_config])

    if ue_config:
        cmd.extend(["-u", ue_config])

    if container:
        cmd.extend(["-c", container])

    try:
        logger.info(f"執行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"應用配置時發生錯誤: {str(e)}")
        return {
            "stdout": e.stdout,
            "stderr": e.stderr,
            "returncode": e.returncode,
            "error": str(e),
        }


# 路由
@app.get("/", response_model=ConfigResponse)
async def root():
    """API根路由"""
    return ConfigResponse(
        success=True, message="UERANSIM配置API服務運行中", data={"api_version": "1.0.0"}
    )


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus 指標端點"""
    # 簡單的指標示例
    metrics_text = """
# HELP config_api_requests_total 總請求數
# TYPE config_api_requests_total counter
config_api_requests_total 42

# HELP config_api_templates_count 配置模板數量
# TYPE config_api_templates_count gauge
config_api_templates_count {0}

# HELP config_api_configs_count 生成配置數量
# TYPE config_api_configs_count gauge
config_api_configs_count {1}
""".format(
        len(get_config_templates()), len(get_generated_configs())
    )

    return metrics_text


@app.get("/templates", response_model=ConfigResponse)
async def list_templates():
    """列出所有可用的配置模板"""
    templates = get_config_templates()
    return ConfigResponse(
        success=True,
        message=f"找到 {len(templates)} 個配置模板",
        data={"templates": templates},
    )


@app.get("/configs", response_model=ConfigResponse)
async def list_configs():
    """列出所有生成的配置文件"""
    configs = get_generated_configs()
    return ConfigResponse(
        success=True,
        message=f"找到 {len(configs)} 個生成的配置",
        data={"configs": configs},
    )


@app.get("/template/{template_name}", response_model=ConfigResponse)
async def get_template(template_name: str = Path(..., description="模板名稱")):
    """獲取特定模板的詳細信息"""
    template_path = os.path.join(UERANSIM_CONFIG_DIR, f"{template_name}.yaml")

    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail=f"模板 {template_name} 不存在")

    try:
        with open(template_path, "r") as f:
            content = yaml.safe_load(f)

        return ConfigResponse(
            success=True,
            message=f"成功獲取模板 {template_name}",
            data={"name": template_name, "path": template_path, "content": content},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取模板時出錯: {str(e)}")


@app.post("/generate", response_model=ConfigResponse)
async def generate_config_from_template(
    template_name: str = Query(..., description="模板名稱"),
    config_name: str = Query(..., description="生成的配置名稱"),
    parameters: Dict = Body(..., description="配置參數"),
):
    """基於模板生成新的配置文件"""
    template_path = os.path.join(UERANSIM_CONFIG_DIR, f"{template_name}.yaml")

    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail=f"模板 {template_name} 不存在")

    # 添加時間戳，確保唯一性
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(GENERATED_CONFIG_DIR, f"{config_name}_{timestamp}.yaml")

    try:
        generated_path = generate_config(template_path, parameters, output_path)

        # 創建一個指向最新配置的符號鏈接
        latest_path = os.path.join(GENERATED_CONFIG_DIR, f"{config_name}_latest.yaml")
        if os.path.exists(latest_path):
            os.remove(latest_path)
        os.symlink(generated_path, latest_path)

        return ConfigResponse(
            success=True,
            message=f"成功基於模板 {template_name} 生成配置",
            data={
                "config_path": generated_path,
                "latest_path": latest_path,
                "parameters": parameters,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成配置時出錯: {str(e)}")


@app.post("/apply", response_model=ConfigResponse)
async def apply_config_to_containers(request: ApplyConfigRequest):
    """應用配置到UERANSIM容器"""
    try:
        result = apply_config(request.gnb_config, request.ue_config, request.container)

        if result.get("returncode", 1) != 0:
            return ConfigResponse(success=False, message="應用配置失敗", data=result)

        return ConfigResponse(
            success=True, message="成功應用配置到UERANSIM容器", data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"應用配置時出錯: {str(e)}")


# 啟動函數，用於獨立運行
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
