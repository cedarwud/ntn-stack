#!/usr/bin/env python3
"""
5G NTN 外部連接代理API
此服務為UE提供對外網絡連接的代理服務
"""

import os
import json
import requests
import subprocess
from urllib.parse import urlparse
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="5G NTN 外部連接代理API")

# 啟用CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API根端點"""
    return {"message": "5G NTN 外部連接代理API正在運行"}

@app.get("/api/status")
async def status():
    """API狀態檢查"""
    return {
        "status": "running",
        "version": "1.0.0",
        "timestamp": subprocess.check_output("date").decode().strip()
    }

@app.get("/api/network/info")
async def network_info():
    """獲取網絡信息"""
    try:
        # 獲取網絡接口信息
        ifaces = subprocess.check_output("ip a", shell=True).decode()
        
        # 獲取路由表
        routes = subprocess.check_output("ip route", shell=True).decode()
        
        # 獲取主機名
        hostname = subprocess.check_output("hostname", shell=True).decode().strip()
        
        # 嘗試獲取外部IP
        try:
            external_ip = requests.get("https://api.ipify.org").text
        except:
            external_ip = "無法獲取"
        
        return {
            "hostname": hostname,
            "interfaces": ifaces,
            "routes": routes,
            "external_ip": external_ip
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/proxy/ping")
async def proxy_ping(target: str = "8.8.8.8", count: int = 4):
    """代理ping請求"""
    try:
        result = subprocess.check_output(
            f"ping -c {count} {target}", 
            shell=True
        ).decode()
        return {"result": result}
    except subprocess.CalledProcessError as e:
        return {"error": f"Ping失敗: {str(e)}", "output": e.output.decode() if e.output else "無輸出"}

@app.get("/api/proxy/http")
async def proxy_http(url: str):
    """代理HTTP請求"""
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="無效的URL")
        
        response = requests.get(url, timeout=10)
        
        headers = dict(response.headers)
        content = response.content
        
        return JSONResponse(
            content={
                "status_code": response.status_code,
                "headers": headers,
                "content": content.decode('utf-8', errors='replace'),
                "url": url,
            },
            status_code=response.status_code
        )
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/proxy/dns")
async def proxy_dns(domain: str):
    """代理DNS解析"""
    try:
        result = subprocess.check_output(
            f"dig {domain} +short", 
            shell=True
        ).decode()
        return {"domain": domain, "result": result}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
