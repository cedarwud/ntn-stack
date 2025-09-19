#!/usr/bin/env python3
"""修復測試TLE數據的校驗和"""

def calculate_tle_checksum(tle_line):
    """計算TLE行的校驗和"""
    if len(tle_line) != 69:
        return None

    checksum = 0
    for char in tle_line[:-1]:  # 排除最後一位校驗和
        if char.isdigit():
            checksum += int(char)
        elif char == '-':
            checksum += 1

    return checksum % 10

def fix_tle_checksum(tle_line):
    """修復TLE行的校驗和"""
    if len(tle_line) != 69:
        return tle_line

    correct_checksum = calculate_tle_checksum(tle_line)
    return tle_line[:-1] + str(correct_checksum)

# 測試數據
test_lines = [
    '1 12345U 24001A   25261.50000000  .00000000  00000-0  00000-0 0  9999',
    '2 12345  53.0000 120.0000 0000000  90.0000 270.0000 15.50000000000009'
]

print("修復後的TLE數據:")
for line in test_lines:
    fixed_line = fix_tle_checksum(line)
    print(f"'{fixed_line}',")

# 動態生成的測試數據
print("\n動態生成測試數據修復:")
for i in range(5):
    line1 = f'1 {12345+i:05d}U 24001A   25261.50000000  .00000000  00000-0  00000-0 0  999{i%10}'
    line2 = f'2 {12345+i:05d}  53.0000 {120.0+i*10:.4f} 0000000  90.0000 270.0000 15.50000000000009'

    fixed_line1 = fix_tle_checksum(line1)
    fixed_line2 = fix_tle_checksum(line2)

    print(f"  衛星 {i}: Line1 = '{fixed_line1}'")
    print(f"  衛星 {i}: Line2 = '{fixed_line2}'")
    print()