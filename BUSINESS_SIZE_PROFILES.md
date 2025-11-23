# Business Size Profiles

## Overview

The EDI generators support automatic volume generation based on business size profiles. This allows you to generate realistic data volumes without specifying exact counts.

## Business Sizes

### Small Business
- **834 (Enrollment)**: 50-200 members
- **837 (Claims)**: 10-50 claims/day
- **835 (Payments)**: ~60% of claims (paid), 20% denied, 20% pending

### Medium Business
- **834 (Enrollment)**: 500-3,000 members
- **837 (Claims)**: 100-1,000 claims/day
- **835 (Payments)**: ~60% of claims (paid), 20% denied, 20% pending

### Large Business
- **834 (Enrollment)**: 10,000-50,000 members
- **837 (Claims)**: 2,000-10,000 claims/day
- **835 (Payments)**: ~60% of claims (paid), 20% denied, 20% pending

## Usage

### Automatic Volume Generation

```python
from src.edi.generator import generate_edi_834, generate_edi_837, generate_edi_835

# Small business
generate_edi_834(business_size="small")
generate_edi_837(business_size="small")
generate_edi_835(business_size="small")

# Medium business (default)
generate_edi_834(business_size="medium")
generate_edi_837(business_size="medium")

# Large business
generate_edi_834(business_size="large")
generate_edi_837(business_size="large")
```

### Manual Override

You can still specify exact counts when needed:

```python
# Override with exact count
generate_edi_834(num_members=500, business_size="small")  # Uses 500, ignores business_size

# Or just specify directly
generate_edi_837(num_claims=500)  # Uses 500 claims
```

### Batch Generation

```python
from src.edi.generator import generate_edi_files

# Generate all files for small business
generate_edi_files(format="csv", business_size="small")

# Generate all files for large business
generate_edi_files(format="x12", business_size="large")
```

## Statistical Distributions

The system uses different statistical distributions for realistic volume generation:

- **Uniform Distribution**: Used for small business ranges
- **Poisson Distribution**: Used for claim volumes (small business)
- **Log-Normal Distribution**: Used for medium and large business volumes (more realistic for business data)

All generated volumes are clamped to the defined min/max ranges to ensure realistic values.

## Payment Ratios

For EDI 835 (payments), the system automatically calculates payment volumes based on:
- **60% Paid**: Claims that are approved and paid
- **20% Denied**: Claims that are denied
- **20% Pending**: Claims still in process

If claims exist, payments are calculated as 60% of total claims. If no claims exist, payments are generated based on the business size profile.

