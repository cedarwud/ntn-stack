const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const axios = require('axios');
const { createProxyMiddleware } = require('http-proxy-middleware');

// 創建Express應用
const app = express();
const port = process.env.PORT || 3000;

// 配置中間件
app.use(morgan('combined'));
app.use(cors());
app.use(express.json());

// 健康檢查端點
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'ntn-proxy' });
});

// API路由
app.get('/api', (req, res) => {
  res.json({
    service: 'NTN Proxy Service',
    version: '1.0.0',
    endpoints: [
      '/api/proxy/http - HTTP代理服務',
      '/api/dns - DNS解析服務',
      '/api/ping - Ping測試服務'
    ]
  });
});

// HTTP代理服務
app.get('/api/proxy/http', async (req, res) => {
  const url = req.query.url;

  if (!url) {
    return res.status(400).json({ error: '缺少URL參數' });
  }

  try {
    const response = await axios.get(url);
    res.json({
      success: true,
      data: response.data,
      status: response.status,
      headers: response.headers
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      status: error.response ? error.response.status : null
    });
  }
});

// DNS解析服務
app.get('/api/dns', (req, res) => {
  const hostname = req.query.hostname;

  if (!hostname) {
    return res.status(400).json({ error: '缺少hostname參數' });
  }

  require('dns').lookup(hostname, (err, address, family) => {
    if (err) {
      return res.status(500).json({
        success: false,
        error: err.message
      });
    }

    res.json({
      success: true,
      hostname: hostname,
      ip: address,
      ipVersion: family
    });
  });
});

// Ping測試服務
app.get('/api/ping', (req, res) => {
  const target = req.query.target || '8.8.8.8';
  const count = req.query.count || 4;

  const ping = require('child_process').spawn('ping', ['-c', count, target]);

  let pingOutput = '';

  ping.stdout.on('data', (data) => {
    pingOutput += data.toString();
  });

  ping.on('close', (code) => {
    if (code === 0) {
      // 提取平均延遲
      const avgMatch = pingOutput.match(/min\/avg\/max(?:\/mdev)?\s+=\s+[\d.]+\/(?<avg>[\d.]+)\/[\d.]+(?:\/[\d.]+)?/);
      const avgLatency = avgMatch ? parseFloat(avgMatch.groups.avg) : null;

      // 提取丟包率
      const lossMatch = pingOutput.match(/(\d+)% packet loss/);
      const packetLoss = lossMatch ? parseInt(lossMatch[1]) : null;

      res.json({
        success: true,
        target: target,
        count: count,
        avgLatency: avgLatency,
        packetLoss: packetLoss,
        output: pingOutput
      });
    } else {
      res.status(500).json({
        success: false,
        error: 'Ping命令失敗',
        output: pingOutput
      });
    }
  });
});

// 指標端點
app.get('/api/v1/metrics', (req, res) => {
  res.set('Content-Type', 'text/plain');
  res.send(`
# HELP ntn_proxy_requests_total Total number of HTTP requests
# TYPE ntn_proxy_requests_total counter
ntn_proxy_requests_total 42

# HELP ntn_proxy_request_duration_milliseconds HTTP request latency
# TYPE ntn_proxy_request_duration_milliseconds histogram
ntn_proxy_request_duration_milliseconds_bucket{le="50"} 32
ntn_proxy_request_duration_milliseconds_bucket{le="100"} 35
ntn_proxy_request_duration_milliseconds_bucket{le="200"} 38
ntn_proxy_request_duration_milliseconds_bucket{le="500"} 40
ntn_proxy_request_duration_milliseconds_bucket{le="1000"} 41
ntn_proxy_request_duration_milliseconds_bucket{le="+Inf"} 42
`);
});

// 啟動服務器
app.listen(port, () => {
  console.log(`NTN Proxy Service 運行在 http://localhost:${port}`);
}); 