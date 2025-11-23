# Risk Profile Configuration

## Overview

The EDI 837 generator supports risk-based data generation to create realistic claim distributions that match different patient populations and healthcare scenarios.

## Risk Profiles

### High Risk Profile

**Characteristics:**
- 70% chronic diseases
- 60% multiple diagnosis codes
- 30% ER visits
- 50% high-cost claims (>$5000)
- 25% denial rate
- High service line complexity (3-8 lines per claim)
- Charge range: $500-$15,000

**Use Cases:**
- Testing high-cost claim processing
- Chronic disease management scenarios
- Emergency care patterns
- Complex claim adjudication

### Low Risk Profile

**Characteristics:**
- 10% chronic diseases
- 20% multiple diagnosis codes
- 2% ER visits
- 10% high-cost claims
- 5% denial rate
- Low service line complexity (1-2 lines per claim)
- Charge range: $50-$500

**Use Cases:**
- Preventive care scenarios
- Routine office visits
- Low-cost claim processing
- Healthy population modeling

### Balanced Profile (Default)

**Characteristics:**
- 30% chronic diseases
- 40% multiple diagnosis codes
- 10% ER visits
- 25% high-cost claims
- 15% denial rate
- Medium service line complexity (2-5 lines per claim)
- Charge range: $100-$5,000

**Use Cases:**
- General population modeling
- Mixed claim scenarios
- Standard testing

## Usage

### Basic Usage

```python
from src.edi.generator import generate_edi_837

# High risk profile
result = generate_edi_837(
    num_claims=100,
    risk_profile="high_risk",
    format="csv"
)

# Low risk profile
result = generate_edi_837(
    num_claims=100,
    risk_profile="low_risk",
    format="csv"
)

# Balanced profile (default)
result = generate_edi_837(
    num_claims=100,
    risk_profile="balanced",
    format="csv"
)
```

### Custom Distribution

Override specific parameters from a base profile:

```python
# Custom distribution overriding balanced profile
result = generate_edi_837(
    num_claims=100,
    risk_profile="balanced",
    custom_distribution={
        "high_cost_ratio": 0.3,      # 30% high-cost claims
        "denial_rate": 0.15,         # 15% denied
        "er_visit_rate": 0.1,        # 10% ER visits
        "charge_range": (200, 8000), # Custom charge range
    },
    format="csv"
)
```

### Combined with Business Size

```python
# High risk, medium business
result = generate_edi_837(
    business_size="medium",
    risk_profile="high_risk",
    format="csv"
)
```

## Custom Distribution Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `chronic_disease_rate` | float | Rate of chronic disease diagnoses | 0.7 (70%) |
| `multiple_diagnosis_rate` | float | Rate of claims with multiple diagnoses | 0.6 (60%) |
| `er_visit_rate` | float | Rate of ER visits | 0.3 (30%) |
| `high_cost_ratio` | float | Rate of high-cost claims | 0.5 (50%) |
| `denial_rate` | float | Rate of denied claims | 0.25 (25%) |
| `service_line_complexity` | string | 'high', 'medium', or 'low' | 'high' |
| `charge_range` | tuple | (min, max) charge range | (500, 15000) |
| `diagnosis_weights` | dict | Weights for chronic/acute/preventive | {'chronic': 0.7, 'acute': 0.2, 'preventive': 0.1} |
| `provider_types` | dict | Distribution of provider types | {'emergency': 0.3, 'specialist': 0.4, 'primary': 0.3} |

## Automatic Adjustments

The generator automatically adjusts:

1. **Diagnosis Codes**: Based on `diagnosis_weights`, selects from appropriate pools:
   - Chronic: Diabetes, hypertension, COPD, etc.
   - Acute: Pneumonia, infections, etc.
   - Preventive: Routine exams, screenings

2. **Provider Types**: Based on `provider_types` distribution:
   - Emergency: ER visits
   - Specialist: Specialized care
   - Primary: Routine care

3. **Service Line Complexity**: Based on `service_line_complexity`:
   - High: 3-8 service lines
   - Medium: 2-5 service lines
   - Low: 1-2 service lines

4. **Total Charges**: Based on `charge_range` and `high_cost_ratio`:
   - High-cost claims: 60-100% of max range
   - Normal claims: min to 60% of max range

5. **Claim Status**: Based on `denial_rate`:
   - Denied: Status codes 19, 20, 21, 22
   - Paid/Pending: Status codes 1, 2, 3, 4

## Examples

### High-Risk Population

```python
result = generate_edi_837(
    num_claims=500,
    risk_profile="high_risk",
    format="csv"
)

# Analyze results
high_cost = sum(1 for r in result['data'] if float(r['billed_amount']) > 5000)
er_visits = sum(1 for r in result['data'] if r['location_type'] == 'ER')
print(f"High-cost claims: {high_cost/len(result['data']):.1%}")
print(f"ER visits: {er_visits/len(result['data']):.1%}")
```

### Custom Scenario

```python
# Custom scenario: High ER visits but low denial rate
result = generate_edi_837(
    num_claims=200,
    risk_profile="balanced",
    custom_distribution={
        "er_visit_rate": 0.4,    # 40% ER visits
        "denial_rate": 0.05,      # Only 5% denied
        "high_cost_ratio": 0.6,   # 60% high-cost
    },
    format="csv"
)
```

## Integration with Other Features

Risk profiles work seamlessly with:

- **Business Size Profiles**: Combine volume and risk characteristics
- **Invalid Data Generation**: Add data quality issues on top of risk profiles
- **CSV/X12 Formats**: Works with both output formats

```python
# Complete example
result = generate_edi_837(
    business_size="medium",
    risk_profile="high_risk",
    invalid_rate=0.05,
    format="csv"
)
```

