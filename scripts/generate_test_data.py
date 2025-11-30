#!/usr/bin/env python3
"""
Generate test data for claim-management-system pipeline
按照 S3 raw bucket 的路径规范生成测试数据

路径格式: <source_system>/dt=<YYYY-MM-DD>/<filename>.<ext>
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.edi.generator import generate_edi_834, generate_edi_837, generate_edi_835


def generate_test_data(
    output_dir: str = None,
    date_str: str = None,
    num_members: int = 50,
    num_claims: int = 100,
    num_payments: int = 80,
    formats: list = None
):
    """
    Generate test data files organized by source system and date
    
    Args:
        output_dir: Base output directory (default: data/pipeline_test)
        date_str: Date string in YYYY-MM-DD format (default: today)
        num_members: Number of enrollment records
        num_claims: Number of claim records
        num_payments: Number of payment records
        formats: List of formats to generate ['csv', 'x12'] (default: both)
    """
    # Default values
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'pipeline_test'
        )
    
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    if formats is None:
        formats = ['csv', 'x12']
    
    print(f"=" * 60)
    print(f"Generating test data for claim-management-system")
    print(f"=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Date partition: dt={date_str}")
    print(f"Formats: {formats}")
    print(f"Records: {num_members} members, {num_claims} claims, {num_payments} payments")
    print(f"=" * 60)
    
    # Create directory structure
    # enrollment/dt=YYYY-MM-DD/
    # claims/dt=YYYY-MM-DD/
    # payments/dt=YYYY-MM-DD/
    
    source_systems = ['enrollment', 'claims', 'payments']
    for source_system in source_systems:
        dir_path = os.path.join(output_dir, source_system, f'dt={date_str}')
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generate files for each format
    for fmt in formats:
        ext = 'csv' if fmt == 'csv' else 'txt'
        
        print(f"\n--- Generating {fmt.upper()} format files ---")
        
        # 1. Generate 834 (Enrollment)
        enrollment_file = os.path.join(
            output_dir, 'enrollment', f'dt={date_str}',
            f'enrollment_834_{timestamp}.{ext}'
        )
        print(f"\nGenerating 834 (Enrollment): {enrollment_file}")
        generate_edi_834(
            num_members=num_members,
            output_file=enrollment_file,
            format=fmt,
            business_size="small"
        )
        print(f"✓ Created: {enrollment_file}")
        
        # 2. Generate 837 (Claims)
        claims_file = os.path.join(
            output_dir, 'claims', f'dt={date_str}',
            f'claims_837_{timestamp}.{ext}'
        )
        print(f"\nGenerating 837 (Claims): {claims_file}")
        generate_edi_837(
            num_claims=num_claims,
            output_file=claims_file,
            format=fmt,
            business_size="small"
        )
        print(f"✓ Created: {claims_file}")
        
        # 3. Generate 835 (Payments)
        payments_file = os.path.join(
            output_dir, 'payments', f'dt={date_str}',
            f'payments_835_{timestamp}.{ext}'
        )
        print(f"\nGenerating 835 (Payments): {payments_file}")
        generate_edi_835(
            num_payments=num_payments,
            output_file=payments_file,
            format=fmt,
            business_size="small"
        )
        print(f"✓ Created: {payments_file}")
    
    print(f"\n" + "=" * 60)
    print(f"✓ All test data generated successfully!")
    print(f"=" * 60)
    
    # Print upload instructions
    print(f"\n--- Upload to S3 ---")
    print(f"To upload these files to S3, run:")
    print(f"")
    print(f"# Set your bucket name")
    print(f"BUCKET=claim-management-raw")
    print(f"")
    print(f"# Upload all files")
    print(f"aws s3 sync {output_dir}/ s3://$BUCKET/")
    print(f"")
    print(f"# Or upload individually:")
    for source_system in source_systems:
        print(f"aws s3 sync {output_dir}/{source_system}/ s3://$BUCKET/{source_system}/")
    
    return output_dir


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for claim-management-system')
    parser.add_argument('--date', type=str, default=None,
                        help='Date partition (YYYY-MM-DD), default: today')
    parser.add_argument('--members', type=int, default=50,
                        help='Number of enrollment records (default: 50)')
    parser.add_argument('--claims', type=int, default=100,
                        help='Number of claim records (default: 100)')
    parser.add_argument('--payments', type=int, default=80,
                        help='Number of payment records (default: 80)')
    parser.add_argument('--format', type=str, choices=['csv', 'x12', 'both'], default='both',
                        help='Output format (default: both)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory (default: data/pipeline_test)')
    
    args = parser.parse_args()
    
    # Determine formats
    if args.format == 'both':
        formats = ['csv', 'x12']
    else:
        formats = [args.format]
    
    # Generate data
    generate_test_data(
        output_dir=args.output,
        date_str=args.date,
        num_members=args.members,
        num_claims=args.claims,
        num_payments=args.payments,
        formats=formats
    )

