#!/usr/bin/env python3
"""
Generate HIGH RISK patient test data for testing the High-Risk Patient Alert System

This script generates data with:
- High-cost claims (>$10,000)
- Multiple ER visits per member
- Chronic disease diagnosis codes (E11=Diabetes, I25=Heart Disease, J44=COPD, etc.)
- Multiple claims per member to trigger risk scoring
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.edi.generator import generate_edi_834, generate_edi_837, generate_edi_835


def generate_high_risk_test_data(
    output_dir: str = None,
    date_str: str = None,
    num_members: int = 20,  # Small group of high-risk members
    claims_per_member: int = 8,  # Many claims per member (to exceed thresholds)
):
    """
    Generate high-risk patient test data
    
    This creates:
    - 20 members enrolled
    - 160 claims (8 per member) with high_risk profile
      - High costs ($500-$15,000 per claim)
      - 30% ER visits
      - 70% chronic disease diagnoses
    - 100+ payments
    """
    # Default values
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'high_risk_test'
        )
    
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    num_claims = num_members * claims_per_member
    num_payments = int(num_claims * 0.7)  # 70% of claims get paid
    
    print("=" * 70)
    print("🚨 GENERATING HIGH-RISK PATIENT TEST DATA")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print(f"Date partition: dt={date_str}")
    print(f"Members: {num_members}")
    print(f"Claims: {num_claims} ({claims_per_member} per member)")
    print(f"Payments: {num_payments}")
    print(f"Risk Profile: HIGH_RISK")
    print("  - 70% chronic disease diagnoses")
    print("  - 30% ER visits")
    print("  - 50% high-cost claims ($500-$15,000)")
    print("=" * 70)
    
    # Create directory structure
    source_systems = ['enrollment', 'claims', 'payments']
    for source_system in source_systems:
        dir_path = os.path.join(output_dir, source_system, f'dt={date_str}')
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generate CSV format only (simpler for testing)
    fmt = 'csv'
    ext = 'csv'
    
    print(f"\n--- Generating HIGH-RISK CSV files ---")
    
    # 1. Generate 834 (Enrollment) - Normal enrollment
    enrollment_file = os.path.join(
        output_dir, 'enrollment', f'dt={date_str}',
        f'enrollment_high_risk_{timestamp}.{ext}'
    )
    print(f"\n📋 Generating 834 (Enrollment): {enrollment_file}")
    generate_edi_834(
        num_members=num_members,
        output_file=enrollment_file,
        format=fmt,
        business_size="small"
    )
    print(f"✓ Created: {enrollment_file}")
    
    # 2. Generate 837 (Claims) with HIGH RISK profile
    claims_file = os.path.join(
        output_dir, 'claims', f'dt={date_str}',
        f'claims_high_risk_{timestamp}.{ext}'
    )
    print(f"\n🏥 Generating 837 (Claims) with HIGH RISK profile: {claims_file}")
    generate_edi_837(
        num_claims=num_claims,
        output_file=claims_file,
        format=fmt,
        business_size="small",
        risk_profile="high_risk"  # ← KEY: Use high_risk profile
    )
    print(f"✓ Created: {claims_file}")
    
    # 3. Generate 835 (Payments)
    payments_file = os.path.join(
        output_dir, 'payments', f'dt={date_str}',
        f'payments_high_risk_{timestamp}.{ext}'
    )
    print(f"\n💰 Generating 835 (Payments): {payments_file}")
    generate_edi_835(
        num_payments=num_payments,
        output_file=payments_file,
        format=fmt,
        business_size="small"
    )
    print(f"✓ Created: {payments_file}")
    
    print(f"\n" + "=" * 70)
    print(f"✓ HIGH-RISK test data generated successfully!")
    print("=" * 70)
    
    # Print upload instructions
    print(f"\n--- Upload to S3 ---")
    print(f"aws s3 sync {output_dir}/ s3://claim-management-raw/")
    
    return output_dir


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate HIGH-RISK patient test data')
    parser.add_argument('--date', type=str, default=None,
                        help='Date partition (YYYY-MM-DD), default: today')
    parser.add_argument('--members', type=int, default=20,
                        help='Number of members (default: 20)')
    parser.add_argument('--claims-per-member', type=int, default=8,
                        help='Claims per member (default: 8)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory')
    
    args = parser.parse_args()
    
    generate_high_risk_test_data(
        output_dir=args.output,
        date_str=args.date,
        num_members=args.members,
        claims_per_member=args.claims_per_member
    )

