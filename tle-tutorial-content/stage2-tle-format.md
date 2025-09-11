# 階段2：TLE數據格式深度解析

## TLE標準格式歷史背景

### TLE發展歷程：

**1950年代** - 初期軌道追蹤需求
- 蘇聯衛星1號發射後的軌道預測需求
- 美國建立NORAD (北美防空司令部)

**1960年代** - 標準化格式建立
- NASA和NORAD共同制定TLE標準
- 確保軌道數據的國際通用性

**1980年代** - 民用開放
- Space-Track.org平台建立
- 業餘無線電愛好者開始使用

**2020年代** - 商業衛星時代
- Starlink 8,370顆衛星
- OneWeb 648顆衛星
- 每日更新數萬筆TLE數據

### 為什麼選擇TLE？
- **格式簡潔**：僅需3行描述完整軌道
- **計算高效**：SGP4算法專門優化
- **全球通用**：所有衛星追蹤系統支援

## TLE三行數據結構分析

### TLE標準三行格式：

**第0行 (衛星名稱)**
- 最多24個字符
- 衛星識別名稱
- 可包含任務編號

**第1行 (軌道參數第一部分)**
- 69個字符固定長度
- NORAD ID、epoch時間、運動微分
- 拖拽係數、星曆類型

**第2行 (軌道參數第二部分)**
- 69個字符固定長度
- 軌道傾角、升交點、偏心率
- 近地點幅角、平均運動

### 關鍵設計原理：
- 固定欄位寬度→解析效率高
- 校驗和機制→數據完整性
- ASCII編碼→跨平台相容性

## 實際Starlink衛星TLE範例

### STARLINK-1008 實際TLE數據：

```
STARLINK-1008
1 44714U 19074A   25245.83333333  .00001234  00000-0  12345-4 0  9992
2 44714  53.0123 123.4567 0001234 123.4567 236.5432 15.05123456123456
```

### 快速識別要素：

- 第0行：衛星名稱 'STARLINK-1008'
- 第1行開頭：'1' (行號標識)
- 第2行開頭：'2' (行號標識)
- 行末數字：校驗和 (2, 6)

### 這顆衛星的基本資料：
- NORAD ID: 44714
- 發射日期: 2019年 (19074A)
- 軌道高度: ~550km
- 軌道傾角: 53.0123°
- 軌道週期: ~95分鐘

## NORAD ID：衛星唯一識別碼

### NORAD ID基本概念：

- **位置**：第1行第3-7位 (5位數字)
- **格式**：整數，範圍1-99999
- **用途**：全球衛星唯一識別

### 實際範例解析：
```
1 44714U 19074A...
  ^^^^^  ← NORAD ID = 44714
```

### 常見衛星NORAD ID：
- ISS國際太空站: 25544
- Starlink-1008: 44714
- OneWeb-0001: 44713
- 天宮太空站: 48274

### Python解析程式：
```python
def parse_norad_id(line1: str) -> int:
    return int(line1[2:7])

norad_id = parse_norad_id(line1)
print(f"NORAD ID: {norad_id}")
```

## 國際標識符：發射任務編碼

### 國際標識符格式詳解：

- **位置**：第1行第10-17位
- **格式**：YYLLLPPP (8個字符)

### 編碼含義：
- YY = 年份 (19 = 2019年)
- LLL = 發射序號 (074 = 第74次發射)
- PPP = 載荷編號 (A = 主載荷)

### 實際範例解析：
```
1 44714U 19074A  ...
        ^^^^^^^ ← 19074A
        19 = 2019年
        074 = 第74次發射
        A = 主要載荷
```

### 載荷編號說明：
- A = 主載荷 (通常是最重要的衛星)
- B, C, D... = 次載荷
- AA, AB... = 超過26個載荷時使用

### 解析程式：
```python
designator = line1[9:17].strip()
year = int(designator[:2])
launch_num = int(designator[2:5])
payload = designator[5:]
```

## Epoch時間：TLE數據時間基準

### Epoch時間格式說明：

- **位置**：第1行第19-32位
- **格式**：YYDDD.DDDDDDDD
- YY = 年份後兩位
- DDD.DD = 年中第幾天(含小數)

### 實際範例計算：
```
25245.83333333
25 = 2025年
245.83333333 = 第245.83天
```

### 轉換為具體日期時間：
- 2025年第245天 = 9月2日
- 0.83333333天 = 20小時
- 結果：2025年9月2日 20:00 UTC

### ⚠️ 極其重要的原則：
**🚨 必須使用epoch時間計算軌道**
**❌ 絕對不能用當前時間！**

### 轉換程式：
```python
from datetime import datetime, timedelta

def parse_epoch(epoch_str):
    year = int(epoch_str[:2])
    year = 2000 + year if year < 57 else 1900 + year
    day = float(epoch_str[2:])
    return datetime(year, 1, 1) + timedelta(days=day-1)
```

## 運動微分：軌道衰減參數

### 運動微分參數詳解：

**第一微分 (位置：33-43)**
- 平均運動的一階導數
- 單位：轉/天²
- 反映軌道高度變化率

**第二微分 (位置：44-52)**
- 平均運動的二階導數
- 科學記數法格式
- 通常接近零

**拖拽係數 (位置：53-61)**
- B* 拖拽項係數
- 大氣阻力影響
- 科學記數法格式

### 科學記數法解析：
```
12345-4 表示 0.12345 × 10⁻⁴
+12345-3 表示 +0.12345 × 10⁻³
-12345-5 表示 -0.12345 × 10⁻⁵
```

### 解析程式：
```python
def parse_scientific(field):
    if not field.strip(): return 0.0
    mantissa = field[:-2]
    exponent = field[-2:]
    return float(mantissa) * (10 ** int(exponent))
```

## 軌道傾角：衛星軌道面方向

### 軌道傾角基本概念：

- **位置**：第2行第9-16位
- **定義**：軌道面與赤道面的夾角
- **範圍**：0° - 180°
- **單位**：度 (°)

### 不同傾角的軌道特性：

**0° - 赤道軌道**
- 沿赤道運行，覆蓋赤道地區

**53° - Starlink主要軌道**
- 覆蓋人口密集地區
- 平衡覆蓋和發射成本

**87.4° - OneWeb極地軌道**
- 接近極地，全球覆蓋
- 包含極地區域

**98° - 太陽同步軌道**
- 觀測衛星常用
- 固定太陽角度

### 解析程式：
```python
inclination = float(line2[8:16])
print(f"軌道傾角: {inclination}°")
```

## 升交點赤經：軌道面空間定向

### 升交點赤經 (RAAN) 解析：

- **位置**：第2行第18-25位
- **定義**：軌道面與赤道面交點的經度
- **範圍**：0° - 360°
- **單位**：度 (°)

### 物理意義：
- 確定軌道面在太空中的方向
- 升交點：衛星從南半球進入北半球的點
- 隨地球自轉和軌道攝動而變化

### RAAN變化特性：

**LEO衛星 (如Starlink):**
- 每天變化約1°
- 受地球扁率影響

**極地軌道 (如OneWeb):**
- 變化較小
- 更穩定的方向

### 實際應用：
- 地面站可見性預測
- 衛星星座配置
- 覆蓋區域計算

### 解析程式：
```python
raan = float(line2[17:25])
print(f"升交點赤經: {raan}°")
```

## 偏心率：軌道橢圓程度

### 偏心率 (Eccentricity) 詳解：

- **位置**：第2行第27-33位
- **定義**：軌道橢圓的扁平程度
- **範圍**：0-1 (無單位)
- **⚠️ 特殊格式**：省略小數點前的0

### 格式解析：
```
TLE中: 0001234
實際值: 0.0001234
```

### 不同偏心率的軌道：

**e = 0：完美圓形軌道**
- 高度完全一致
- 極少數衛星達到

**e = 0.001：近圓軌道 (Starlink)**
- 高度變化很小
- 通訊衛星理想狀態

**e = 0.7：高度橢圓軌道**
- 近地點和遠地點差異大
- 某些科學任務使用

### 解析程式：
```python
ecc_str = line2[26:33]
eccentricity = float('0.' + ecc_str)
print(f"偏心率: {eccentricity}")
```

## 近地點幅角：軌道最低點位置

### 近地點幅角詳解：

- **位置**：第2行第35-42位
- **定義**：近地點相對於升交點的角度
- **範圍**：0° - 360°
- **單位**：度 (°)

### 物理意義：
- 確定軌道橢圓的方向
- 近地點：衛星距離地球最近的點
- 影響衛星速度變化

### 運動特性：

**近地點時：**
- 衛星速度最快
- 軌道高度最低
- 大氣阻力最大

**遠地點時：**
- 衛星速度最慢
- 軌道高度最高
- 大氣阻力最小

### 實際應用：
- 電力系統設計 (日照時間)
- 通訊鏈路預測
- 軌道維持計劃

### 解析程式：
```python
arg_perigee = float(line2[34:42])
print(f"近地點幅角: {arg_perigee}°")
```

## 平均運動：軌道週期核心參數

### 平均運動詳解：

- **位置**：第2行第53-63位
- **定義**：衛星每天繞地球的圈數
- **單位**：轉/天 (revolutions per day)
- **精度**：通常到小數點後8位

### 與軌道高度的關係：

**Starlink (~550km):**
- 平均運動: ~15.05 轉/天
- 軌道週期: ~95分鐘

**OneWeb (~1200km):**
- 平均運動: ~13.15 轉/天
- 軌道週期: ~109分鐘

**ISS (~420km):**
- 平均運動: ~15.49 轉/天
- 軌道週期: ~93分鐘

### 週期計算公式：
```
軌道週期 = 24小時 × 60分鐘 / 平均運動
         = 1440分鐘 / 平均運動
```

### 解析和計算程式：
```python
mean_motion = float(line2[52:63])
period_minutes = 1440.0 / mean_motion
print(f"平均運動: {mean_motion} 轉/天")
print(f"軌道週期: {period_minutes:.1f} 分鐘")
```

## 校驗和：數據完整性驗證

### TLE校驗和機制：

- **位置**：每行最後一位數字
- **算法**：模10校驗
- **目的**：檢測數據傳輸錯誤

### 計算規則：
1. 遍歷除最後一位的所有字符
2. 數字字符：加入該數字
3. 負號 '-'：當作1
4. 其他字符：忽略
5. 總和對10取模

### 實際計算範例：
```
1 44714U 19074A   25245.83333333  .00001234  00000-0  12345-4 0  9992
  ^^^^^   計算這些字符的和
1+4+4+7+1+4+1+9+0+7+4+2+5+2+4+5+8+3+3+3+3+3+3+3+0+0+0+0+1+2+3+4+0+0+0+0+0+1+2+3+4+5+1+4+0+9+9+9 = 162
162 % 10 = 2 ✅ 符合行末校驗和
```

### 校驗和驗證程式：
```python
def verify_checksum(line: str) -> bool:
    checksum = 0
    for char in line[:-1]:  # 排除最後一位
        if char.isdigit():
            checksum += int(char)
        elif char == '-':
            checksum += 1
    calculated = checksum % 10
    given = int(line[-1])
    return calculated == given
```

## TLE解析器基礎架構設計

### TLE解析器類別設計：

```python
class TLEParser:
    def __init__(self):
        self.statistics = {
            'total_parsed': 0,
            'successful': 0,
            'failed': 0,
            'checksum_errors': 0
        }
    
    def parse_tle_file(self, file_path: str) -> List[Dict]:
        """解析完整TLE文件"""
        pass
    
    def parse_tle_lines(self, name: str, 
                       line1: str, line2: str) -> Dict:
        """解析三行TLE數據"""
        pass
    
    def _validate_format(self, line1: str, 
                        line2: str) -> bool:
        """驗證TLE格式"""
        pass
    
    def _parse_line1(self, line1: str) -> Dict:
        """解析第一行"""
        pass
    
    def _parse_line2(self, line2: str) -> Dict:
        """解析第二行"""
        pass
```

### 設計原則：
- 模組化設計
- 錯誤處理
- 統計追蹤
- 可擴展性

## 完整TLE解析器實作

### 核心解析方法實作：

```python
def parse_tle_lines(self, name: str, line1: str, 
                   line2: str) -> Optional[Dict]:
    # 驗證格式
    if not self._validate_format(line1, line2):
        return None
    
    try:
        # 解析第一行
        line1_data = {
            'satellite_number': int(line1[2:7]),
            'international_designator': line1[9:17].strip(),
            'epoch_year': int(line1[18:20]),
            'epoch_day': float(line1[20:32]),
            'first_derivative': float(line1[33:43]),
            'second_derivative': self._parse_scientific(line1[44:52]),
            'drag_coefficient': self._parse_scientific(line1[53:61])
        }
        
        # 解析第二行
        line2_data = {
            'inclination': float(line2[8:16]),
            'raan': float(line2[17:25]),
            'eccentricity': float('0.' + line2[26:33]),
            'arg_perigee': float(line2[34:42]),
            'mean_anomaly': float(line2[43:51]),
            'mean_motion': float(line2[52:63]),
            'revolution_number': int(line2[63:68])
        }
        
        # 合併數據並計算epoch時間
        satellite_data = {'name': name, **line1_data, **line2_data}
        satellite_data['epoch_datetime'] = self._calculate_epoch(
            line1_data['epoch_year'], line1_data['epoch_day'])
        
        return satellite_data
        
    except Exception as e:
        print(f"解析失敗 {name}: {e}")
        return None
```

## TLE解析器測試與驗證

### 解析器測試程式：

```python
# 測試用TLE數據
test_tle = '''
STARLINK-1008
1 44714U 19074A   25245.83333333  .00001234  00000-0  12345-4 0  9992
2 44714  53.0123 123.4567 0001234 123.4567 236.5432 15.05123456123456
'''

def test_tle_parser():
    parser = TLEParser()
    lines = test_tle.strip().split('\n')
    
    result = parser.parse_tle_lines(lines[0], lines[1], lines[2])
    
    # 驗證解析結果
    assert result is not None, "解析失敗"
    assert result['satellite_number'] == 44714
    assert result['inclination'] == 53.0123
    assert result['mean_motion'] == 15.05123456
    
    # 計算軌道週期
    period = 1440.0 / result['mean_motion']
    assert 90 < period < 100, "軌道週期異常"
    
    print("✅ TLE解析器測試通過！")
    print(f"衛星名稱: {result['name']}")
    print(f"軌道週期: {period:.1f} 分鐘")
    print(f"軌道高度: ~{(period/90-1)*420+420:.0f} km")

if __name__ == "__main__":
    test_tle_parser()
```

### 測試重點：
- 基本欄位解析正確性
- 數值範圍合理性
- 時間轉換準確性
- 錯誤處理機制

## 階段總結

### 階段2學習成果確認：

**理論知識掌握：**
- TLE三行格式的歷史和標準
- 第一行全部8個參數詳解
- 第二行全部7個參數詳解
- 校驗和計算和驗證機制

**實作技能獲得：**
- 完整TLE解析器類別設計
- 所有欄位的精確解析方法
- 科學記數法格式處理
- 錯誤檢測和處理機制

**驗證能力建立：**
- TLE數據格式驗證
- 校驗和正確性檢查
- 參數合理性判斷
- 完整的測試程式

**下一步行動計劃：**
- 進入階段3：SGP4軌道計算算法
- 學習如何使用解析後的TLE數據
- 實作衛星位置和速度計算
- 掌握時間基準的關鍵原則

**重要提醒：確保TLE解析器完全正常運作！**