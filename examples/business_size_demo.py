#!/usr/bin/env python3
"""
Demo script showing business size profile usage
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.edi.generator import generate_edi_834, generate_edi_837, generate_edi_835, generate_edi_files

def demo_business_sizes():
    """Demonstrate different business sizes"""
    
    print("=" * 60)
    print("Business Size Profile Demo")
    print("=" * 60)
    
    # Small business
    print("\n1. Small Business:")
    print("-" * 60)
    result_834 = generate_edi_834(business_size="small", format="csv")
    print(f"   Generated {len(result_834)} members")
    
    result_837 = generate_edi_837(business_size="small", format="csv")
    print(f"   Generated {len(result_837)} claims")
    
    result_835 = generate_edi_835(business_size="small", format="csv")
    print(f"   Generated {len(result_835)} payments")
    
    # Medium business
    print("\n2. Medium Business:")
    print("-" * 60)
    result_834 = generate_edi_834(business_size="medium", format="csv")
    print(f"   Generated {len(result_834)} members")
    
    result_837 = generate_edi_837(business_size="medium", format="csv")
    print(f"   Generated {len(result_837)} claims")
    
    result_835 = generate_edi_835(business_size="medium", format="csv")
    print(f"   Generated {len(result_835)} payments")
    
    # Large business
    print("\n3. Large Business:")
    print("-" * 60)
    result_834 = generate_edi_834(business_size="large", format="csv")
    print(f"   Generated {len(result_834)} members")
    
    result_837 = generate_edi_837(business_size="large", format="csv")
    print(f"   Generated {len(result_837)} claims")
    
    result_835 = generate_edi_835(business_size="large", format="csv")
    print(f"   Generated {len(result_835)} payments")
    
    # Manual override
    print("\n4. Manual Override:")
    print("-" * 60)
    result_834 = generate_edi_834(num_members=250, format="csv")
    print(f"   Manual: {len(result_834)} members (override business_size)")
    
    result_837 = generate_edi_837(num_claims=75, format="csv")
    print(f"   Manual: {len(result_837)} claims (override business_size)")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)

if __name__ == "__main__":
    demo_business_sizes()

