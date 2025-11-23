#!/usr/bin/env python3
"""
Comprehensive test suite for EDI generator
Tests all features: business sizes, risk profiles, invalid data, formats
"""

import sys
import os
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.edi.generator import (
    generate_edi_834, generate_edi_837, generate_edi_835,
    generate_edi_files, BUSINESS_SIZE_PROFILES, RISK_PROFILES
)

def test_business_sizes():
    """Test business size profiles"""
    print("\n" + "="*60)
    print("测试 1: 业务规模配置")
    print("="*60)
    
    results = {}
    for size in ['small', 'medium', 'large']:
        result = generate_edi_834(business_size=size, format='csv')
        results[size] = result['total_records']
        profile = BUSINESS_SIZE_PROFILES[size]['834']
        min_val, max_val = profile['min'], profile['max']
        
        status = "✓" if min_val <= result['total_records'] <= max_val else "✗"
        print(f"{size:8s}: {result['total_records']:6d} 条记录 (范围: {min_val}-{max_val}) {status}")
    
    return all(
        BUSINESS_SIZE_PROFILES[size]['834']['min'] <= results[size] <= BUSINESS_SIZE_PROFILES[size]['834']['max']
        for size in results
    )


def test_invalid_data():
    """Test invalid data generation"""
    print("\n" + "="*60)
    print("测试 2: 无效数据生成")
    print("="*60)
    
    test_cases = [
        (0.05, "5%"),
        (0.10, "10%"),
        (0.0, "0% (无无效数据)")
    ]
    
    all_passed = True
    for invalid_rate, desc in test_cases:
        result = generate_edi_834(100, format='csv', invalid_rate=invalid_rate)
        actual_rate = result['invalid_rate']
        expected_min = invalid_rate * 0.5  # Allow 50% variance
        expected_max = invalid_rate * 1.5 if invalid_rate > 0 else 0.05
        
        if invalid_rate == 0:
            passed = actual_rate < 0.05  # Should be very low
        else:
            passed = expected_min <= actual_rate <= expected_max
        
        status = "✓" if passed else "✗"
        print(f"{desc:15s}: 目标={invalid_rate:.1%}, 实际={actual_rate:.1%}, 无效记录={result['invalid_records']} {status}")
        if not passed:
            all_passed = False
    
    return all_passed


def test_risk_profiles():
    """Test risk profile configurations"""
    print("\n" + "="*60)
    print("测试 3: 风险配置文件")
    print("="*60)
    
    all_passed = True
    
    # Test high risk
    result_high = generate_edi_837(100, format='csv', risk_profile='high_risk')
    charges_high = [float(r['billed_amount']) for r in result_high['data']]
    er_high = sum(1 for r in result_high['data'] if r['location_type'] == 'ER' or r['facility_type_code'] == '23')
    denied_high = sum(1 for r in result_high['data'] if r['claim_status'] in ['19', '20', '21', '22'])
    avg_charge_high = sum(charges_high) / len(charges_high)
    
    print(f"高风险配置:")
    print(f"  平均费用: ${avg_charge_high:.2f} (期望: >$2000)")
    print(f"  ER访问: {er_high} ({er_high/len(result_high['data']):.1%}, 期望: ~30%)")
    print(f"  拒绝率: {denied_high} ({denied_high/len(result_high['data']):.1%}, 期望: ~25%)")
    
    high_passed = avg_charge_high > 2000 and er_high > 10
    print(f"  状态: {'✓' if high_passed else '✗'}")
    if not high_passed:
        all_passed = False
    
    # Test low risk
    result_low = generate_edi_837(100, format='csv', risk_profile='low_risk')
    charges_low = [float(r['billed_amount']) for r in result_low['data']]
    er_low = sum(1 for r in result_low['data'] if r['location_type'] == 'ER' or r['facility_type_code'] == '23')
    denied_low = sum(1 for r in result_low['data'] if r['claim_status'] in ['19', '20', '21', '22'])
    avg_charge_low = sum(charges_low) / len(charges_low)
    
    print(f"\n低风险配置:")
    print(f"  平均费用: ${avg_charge_low:.2f} (期望: <$500)")
    print(f"  ER访问: {er_low} ({er_low/len(result_low['data']):.1%}, 期望: ~2%)")
    print(f"  拒绝率: {denied_low} ({denied_low/len(result_low['data']):.1%}, 期望: ~5%)")
    
    low_passed = avg_charge_low < 500 and er_low < 10
    print(f"  状态: {'✓' if low_passed else '✗'}")
    if not low_passed:
        all_passed = False
    
    return all_passed


def test_custom_distribution():
    """Test custom distribution parameters"""
    print("\n" + "="*60)
    print("测试 4: 自定义分布参数")
    print("="*60)
    
    custom = {
        'high_cost_ratio': 0.3,
        'denial_rate': 0.15,
        'er_visit_rate': 0.1
    }
    
    result = generate_edi_837(100, format='csv', risk_profile='balanced', custom_distribution=custom)
    
    charges = [float(r['billed_amount']) for r in result['data']]
    er_count = sum(1 for r in result['data'] if r['location_type'] == 'ER' or r['facility_type_code'] == '23')
    denied_count = sum(1 for r in result['data'] if r['claim_status'] in ['19', '20', '21', '22'])
    
    er_rate = er_count / len(result['data'])
    denied_rate = denied_count / len(result['data'])
    
    print(f"自定义配置:")
    print(f"  ER访问率: {er_rate:.1%} (目标: {custom['er_visit_rate']:.1%})")
    print(f"  拒绝率: {denied_rate:.1%} (目标: {custom['denial_rate']:.1%})")
    
    er_passed = abs(er_rate - custom['er_visit_rate']) < 0.1
    denied_passed = abs(denied_rate - custom['denial_rate']) < 0.1
    
    status = "✓" if (er_passed and denied_passed) else "✗"
    print(f"  状态: {status}")
    
    return er_passed and denied_passed


def test_edi_structure():
    """Test EDI file structure and compliance"""
    print("\n" + "="*60)
    print("测试 5: EDI文件结构验证")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    all_passed = True
    
    try:
        # Test 834
        result_834 = generate_edi_834(50, os.path.join(test_dir, 'test_834.txt'), 'x12')
        with open(os.path.join(test_dir, 'test_834.txt'), 'r') as f:
            content_834 = f.read()
            segments_834 = content_834.split('~')
            
        has_isa = any('ISA*' in s for s in segments_834)
        has_iea = any('IEA*' in s for s in segments_834)
        has_st = any('ST*834*' in s for s in segments_834)
        has_se = any('SE*' in s for s in segments_834)
        
        # Check control numbers
        isa_line = [s for s in segments_834 if 'ISA*' in s][0]
        iea_line = [s for s in segments_834 if 'IEA*' in s][0]
        isa_control = isa_line.split('*')[13].rstrip('~').strip()
        iea_control = iea_line.split('*')[2].rstrip('~').strip()
        control_match = isa_control == iea_control
        
        passed_834 = has_isa and has_iea and has_st and has_se and control_match
        print(f"EDI 834: {'✓' if passed_834 else '✗'}")
        print(f"  ISA/IEA控制号匹配: {'✓' if control_match else '✗'}")
        if not passed_834:
            all_passed = False
        
        # Test 837
        result_837 = generate_edi_837(30, 2, os.path.join(test_dir, 'test_837.txt'), 'x12')
        with open(os.path.join(test_dir, 'test_837.txt'), 'r') as f:
            content_837 = f.read()
            segments_837 = content_837.split('~')
            
        has_isa_837 = any('ISA*' in s for s in segments_837)
        has_iea_837 = any('IEA*' in s for s in segments_837)
        has_st_837 = any('ST*837*' in s for s in segments_837)
        clm_count = len([s for s in segments_837 if 'CLM*' in s])
        
        passed_837 = has_isa_837 and has_iea_837 and has_st_837 and clm_count > 0
        print(f"EDI 837: {'✓' if passed_837 else '✗'}")
        print(f"  CLM段数量: {clm_count}")
        if not passed_837:
            all_passed = False
        
        # Test 835
        result_835 = generate_edi_835(20, os.path.join(test_dir, 'test_835.txt'), 'x12')
        with open(os.path.join(test_dir, 'test_835.txt'), 'r') as f:
            content_835 = f.read()
            segments_835 = content_835.split('~')
            
        has_isa_835 = any('ISA*' in s for s in segments_835)
        has_iea_835 = any('IEA*' in s for s in segments_835)
        has_st_835 = any('ST*835*' in s for s in segments_835)
        clp_count = len([s for s in segments_835 if 'CLP*' in s])
        
        passed_835 = has_isa_835 and has_iea_835 and has_st_835 and clp_count > 0
        print(f"EDI 835: {'✓' if passed_835 else '✗'}")
        print(f"  CLP段数量: {clp_count}")
        if not passed_835:
            all_passed = False
            
    finally:
        shutil.rmtree(test_dir)
    
    return all_passed


def test_csv_format():
    """Test CSV format output"""
    print("\n" + "="*60)
    print("测试 6: CSV格式验证")
    print("="*60)
    
    import csv
    
    test_dir = tempfile.mkdtemp()
    all_passed = True
    
    try:
        # Test 834 CSV
        result_834 = generate_edi_834(50, os.path.join(test_dir, 'test_834.csv'), 'csv')
        with open(os.path.join(test_dir, 'test_834.csv'), 'r') as f:
            reader = csv.DictReader(f)
            rows_834 = list(reader)
            headers_834 = reader.fieldnames
        
        required_834 = ['member_id', 'date_of_birth', 'effective_date']
        has_required_834 = all(col in headers_834 for col in required_834)
        print(f"EDI 834 CSV: {'✓' if has_required_834 else '✗'}")
        print(f"  列数: {len(headers_834)}, 行数: {len(rows_834)}")
        if not has_required_834:
            all_passed = False
        
        # Test 837 CSV
        result_837 = generate_edi_837(30, 2, os.path.join(test_dir, 'test_837.csv'), 'csv')
        with open(os.path.join(test_dir, 'test_837.csv'), 'r') as f:
            reader = csv.DictReader(f)
            rows_837 = list(reader)
            headers_837 = reader.fieldnames
        
        required_837 = ['claim_id', 'billed_amount', 'service_date']
        has_required_837 = all(col in headers_837 for col in required_837)
        print(f"EDI 837 CSV: {'✓' if has_required_837 else '✗'}")
        print(f"  列数: {len(headers_837)}, 行数: {len(rows_837)}")
        if not has_required_837:
            all_passed = False
        
        # Test 835 CSV
        result_835 = generate_edi_835(20, os.path.join(test_dir, 'test_835.csv'), 'csv')
        with open(os.path.join(test_dir, 'test_835.csv'), 'r') as f:
            reader = csv.DictReader(f)
            rows_835 = list(reader)
            headers_835 = reader.fieldnames
        
        required_835 = ['payment_id', 'claim_id', 'paid_amount']
        has_required_835 = all(col in headers_835 for col in required_835)
        print(f"EDI 835 CSV: {'✓' if has_required_835 else '✗'}")
        print(f"  列数: {len(headers_835)}, 行数: {len(rows_835)}")
        if not has_required_835:
            all_passed = False
            
    finally:
        shutil.rmtree(test_dir)
    
    return all_passed


def test_combined_features():
    """Test combining multiple features"""
    print("\n" + "="*60)
    print("测试 7: 组合功能测试")
    print("="*60)
    
    # Test: business_size + risk_profile + invalid_rate
    result = generate_edi_837(
        business_size='small',
        risk_profile='high_risk',
        invalid_rate=0.05,
        format='csv'
    )
    
    print(f"组合测试 (small + high_risk + 5% invalid):")
    print(f"  总记录: {result['total_records']}")
    print(f"  无效记录: {result['invalid_records']} ({result['invalid_rate']:.1%})")
    
    # Verify it has data
    has_data = result['total_records'] > 0 and len(result['data']) > 0
    status = "✓" if has_data else "✗"
    print(f"  状态: {status}")
    
    return has_data


def test_metadata_return():
    """Test metadata return format"""
    print("\n" + "="*60)
    print("测试 8: 元数据返回格式")
    print("="*60)
    
    result = generate_edi_834(50, format='csv', invalid_rate=0.05)
    
    required_keys = ['output_file', 'total_records', 'invalid_records', 'invalid_rate', 'data']
    has_all_keys = all(key in result for key in required_keys)
    
    print(f"元数据键: {required_keys}")
    print(f"  包含所有键: {'✓' if has_all_keys else '✗'}")
    print(f"  总记录: {result['total_records']}")
    print(f"  无效记录: {result['invalid_records']}")
    print(f"  无效率: {result['invalid_rate']:.3f}")
    print(f"  数据行数: {len(result['data'])}")
    
    return has_all_keys and result['total_records'] == len(result['data'])


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("EDI生成器全面测试")
    print("="*60)
    
    tests = [
        ("业务规模配置", test_business_sizes),
        ("无效数据生成", test_invalid_data),
        ("风险配置文件", test_risk_profiles),
        ("自定义分布参数", test_custom_distribution),
        ("EDI文件结构", test_edi_structure),
        ("CSV格式验证", test_csv_format),
        ("组合功能测试", test_combined_features),
        ("元数据返回格式", test_metadata_return),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n错误: {name} 测试失败: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

