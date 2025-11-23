import random
import string
import os
import sys
import csv
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
from mimesis import Person, Address, Datetime
from mimesis.builtins import USASpecProvider
import json
from collections import defaultdict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from config.config import COMPANY_ID, SENDER_ID, RECEIVER_ID, ANONYMIZE_DATA, BATCH_SIZE, SAMPLES_DIR

# Initialize data generation tools
fake = Faker('en_US')
person = Person('en')
address = Address('en')
usa = USASpecProvider()

# Health plan data
PLAN_FEATURES = {
    "preventive_care": ["Annual physical examination", "Vaccinations", "Health screenings"],
    "hospitalization": ["Inpatient services", "Surgical expenses", "Emergency services"],
    "prescription_drugs": ["Generic drugs", "Brand-name drugs", "Specialty medications"],
    "mental_health": ["Psychological counseling", "Psychiatric services", "Substance abuse treatment"],
    "maternity_care": ["Prenatal check-ups", "Delivery services", "Postpartum care"]
}

PLAN_DESCRIPTIONS = [
    "Comprehensive health insurance plan offering extensive medical coverage",
    "Affordable health plan suitable for individuals and small businesses",
    "Premium health insurance plan with access to high-quality provider networks and services",
    "Specialized health insurance solutions designed for specific populations",
    "Flexible Health Savings Account (HSA)-compatible plan"
]

HEALTH_PLANS = [
    {
        "id": "DH-P3678B",
        "name": "Gold Plan",
        "type": "PPO",
        "premium": 500.00,
        "deductible": 2000.00,
        "coinsurance": 20,
        "oop_max": 6000.00,
        "features": random.sample(list(PLAN_FEATURES.keys()), 3),
        "description": random.choice(PLAN_DESCRIPTIONS)
    },
    {
        "id": "DH-P3156C",
        "name": "Silver Plan",
        "type": "HMO",
        "premium": 350.00,
        "deductible": 4000.00,
        "coinsurance": 30,
        "oop_max": 8000.00,
        "features": random.sample(list(PLAN_FEATURES.keys()), 3),
        "description": random.choice(PLAN_DESCRIPTIONS)
    },
    {
        "id": "DH-P8768B",
        "name": "Bronze Plan",
        "type": "HDHP",
        "premium": 250.00,
        "deductible": 6000.00,
        "coinsurance": 40,
        "oop_max": 10000.00,
        "features": random.sample(list(PLAN_FEATURES.keys()), 2),
        "description": random.choice(PLAN_DESCRIPTIONS)
    },
    {
        "id": "DH-P3091B",
        "name": "Platinum Plan",
        "type": "EPO",
        "premium": 600.00,
        "deductible": 1000.00,
        "coinsurance": 10,
        "oop_max": 4000.00,
        "features": random.sample(list(PLAN_FEATURES.keys()), 4),
        "description": random.choice(PLAN_DESCRIPTIONS)
    },
    {
        "id": "DH-P3109C",
        "name": "Catastrophic Plan",
        "type": "HDHP",
        "premium": 200.00,
        "deductible": 8000.00,
        "coinsurance": 50,
        "oop_max": 12000.00,
        "features": random.sample(list(PLAN_FEATURES.keys()), 2),
        "description": random.choice(PLAN_DESCRIPTIONS)
    }
]

# Global data storage
global_data = {
    'members': {},
    'providers': {},
    'enrollments': {},
    'claims': {}
}


def generate_id(prefix, length=8):
    """Generate unique ID with checks for existing IDs"""
    while True:
        if ANONYMIZE_DATA and prefix in ["SUB", "PROV"]:
            id = prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        else:
            id = prefix + ''.join(random.choices(string.digits, k=length))

        # Check if ID exists in relevant global data
        if prefix == "SUB" and id not in global_data['members']:
            return id
        elif prefix == "PROV" and id not in global_data['providers']:
            return id
        elif prefix not in ["SUB", "PROV"]:
            return id


class Member:
    def __init__(self):
        self.id = generate_id("SUB")
        self.last_name = person.last_name()
        self.first_name = person.first_name()
        self.gender = random.choice(['M', 'F'])
        self.dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        self.phone = person.telephone()
        self.email = person.email()
        self.street = address.address()
        self.city = address.city()
        self.state = address.state(abbr=True)
        self.zip_code = address.zip_code()
        self.ssn = fake.ssn()
        self.policy_num = generate_id("POL", 8)
        self.plan = random.choice(HEALTH_PLANS)
        self.status_info = self._generate_status()

        # Store to global data
        global_data['members'][self.id] = self

    def _generate_status(self):
        status = random.choices(
            ['A', 'P', 'T', 'S', 'C', 'G', 'V', 'D'],
            weights=[85, 5, 5, 1, 1, 1, 1, 1]
        )[0]

        if status == 'T':
            reason = random.choice(["07", "28", "43", "33", "25"])
            end_date = fake.date_between(start_date='-1y', end_date='today')
            return (status, reason, end_date)
        return (status, None, None)


class Provider:
    def __init__(self):
        self.id = generate_id("PROV")
        self.last_name = person.last_name()
        self.first_name = person.first_name()
        self.npi = ''.join(random.choices(string.digits, k=10))
        self.tax_id = generate_id("TAX", 9)
        self.street = fake.street_address()
        self.city = fake.city()
        self.state = fake.state_abbr()
        self.zip = fake.zipcode()
        self.taxonomy = random.choice(["207Q00000X", "207R00000X", "208D00000X"])
        self.specialty = random.choice(["Cardiology", "Pediatrics", "Internal Medicine", "Family Practice"])
        self.phone = person.telephone()
        self.email = person.email()
        self.is_in_network = random.choice([True, False])
        self.doing_business_as = f"{self.last_name} {random.choice(['Medical Group', 'Clinic', 'Specialists'])}"
        self.contracts = json.dumps({
            "contract_type": random.choice(["STANDARD", "PREFERRED", "CAPITATED"]),
            "effective_date": fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d')
        })

        # Store to global data
        global_data['providers'][self.id] = self


class Enrollment:
    def __init__(self, member):
        self.id = generate_id("ENR")
        self.member_id = member.id
        self.plan_id = member.plan["id"]
        self.sponsor_id = generate_id("SPON", 6)
        self.start_date = fake.date_between(start_date='-2y', end_date='today')

        # Set end date based on member status
        status, reason, end_date = member.status_info
        if status == 'T':
            reason_map = {
                "07": "Voluntary termination",
                "28": "Initial enrollment",
                "43": "Change of location",
                "33": "Change of medical information",
                "25": "Change of personal data"
            }

            self.end_date = end_date
            self.status = 'TERMINATED'
            self.termination_reason = reason_map.get(reason, reason)
        else:
            self.end_date = None
            self.status = 'ACTIVE'
            self.termination_reason = None

        self.relationship_code = '18'  # Self
        self.transaction_type = random.choice(['021', '001', '024', '030'])
        self.action_code = random.choice(['2', '4'])
        self.insurance_line = 'HLT'

        # Store to global data
        global_data['enrollments'][self.id] = self


def generate_isa_gs_segments(transaction_type, current_date):
    segments = []
    # Generate ISA control number
    isa_control_num = generate_id("", 9)
    
    # ISA segment
    segments.append(
        "ISA*00*          *00*          *ZZ*{sender}*ZZ*{receiver}*{date}*{time}*U*00401*{control_num}*0*P*:~".format(
            sender=SENDER_ID.ljust(15),
            receiver=RECEIVER_ID.ljust(15),
            date=current_date.strftime("%y%m%d"),
            time=current_date.strftime("%H%M"),
            control_num=isa_control_num
        ))

    # GS segment
    if transaction_type == "834":
        gs_code = "BE"
        version = "004010X095A1"  # Use same version as ST segment
    elif transaction_type == "837":
        gs_code = "HC"
        version = "004010X098A1"
    else:  # 835
        gs_code = "HP"
        version = "004010X091A1"

    segments.append("GS*{gs_code}*{sender}*{receiver}*{date}*{time}*1*X*{version}~".format(
        gs_code=gs_code,
        sender=SENDER_ID,
        receiver=RECEIVER_ID,
        date=current_date.strftime("%Y%m%d"),
        time=current_date.strftime("%H%M%S"),
        version=version
    ))
    return segments, isa_control_num


# Business size volume profiles
BUSINESS_SIZE_PROFILES = {
    'small': {
        '834': {'min': 50, 'max': 200, 'distribution': 'uniform'},
        '837': {'min': 10, 'max': 50, 'distribution': 'poisson', 'lambda': 30},
        '835_ratio': {'paid': 0.6, 'denied': 0.2, 'pending': 0.2}
    },
    'medium': {
        '834': {'min': 500, 'max': 3000, 'distribution': 'lognormal', 'mean': 6.5, 'sigma': 0.5},
        '837': {'min': 100, 'max': 1000, 'distribution': 'lognormal', 'mean': 5.5, 'sigma': 0.6},
        '835_ratio': {'paid': 0.6, 'denied': 0.2, 'pending': 0.2}
    },
    'large': {
        '834': {'min': 10000, 'max': 50000, 'distribution': 'lognormal', 'mean': 10.0, 'sigma': 0.4},
        '837': {'min': 2000, 'max': 10000, 'distribution': 'lognormal', 'mean': 8.0, 'sigma': 0.5},
        '835_ratio': {'paid': 0.6, 'denied': 0.2, 'pending': 0.2}
    }
}

# Risk profile configurations
RISK_PROFILES = {
    'high_risk': {
        'chronic_disease_rate': 0.7,  # 70% chronic diseases
        'multiple_diagnosis_rate': 0.6,  # 60% have multiple diagnoses
        'er_visit_rate': 0.3,  # 30% ER visits
        'high_cost_ratio': 0.5,  # 50% high-cost claims
        'denial_rate': 0.25,  # 25% denied
        'service_line_complexity': 'high',  # More service lines
        'charge_range': (500, 15000),  # Higher charge range
        'diagnosis_weights': {
            'chronic': 0.7,  # Chronic diseases (diabetes, heart disease, etc.)
            'acute': 0.2,
            'preventive': 0.1
        },
        'provider_types': {
            'emergency': 0.3,
            'specialist': 0.4,
            'primary': 0.3
        }
    },
    'low_risk': {
        'chronic_disease_rate': 0.1,  # 10% chronic diseases
        'multiple_diagnosis_rate': 0.2,  # 20% have multiple diagnoses
        'er_visit_rate': 0.02,  # 2% ER visits
        'high_cost_ratio': 0.1,  # 10% high-cost claims
        'denial_rate': 0.05,  # 5% denied
        'service_line_complexity': 'low',  # Fewer service lines
        'charge_range': (50, 500),  # Lower charge range
        'diagnosis_weights': {
            'chronic': 0.1,
            'acute': 0.3,
            'preventive': 0.6  # Mostly preventive
        },
        'provider_types': {
            'emergency': 0.02,
            'specialist': 0.2,
            'primary': 0.78
        }
    },
    'balanced': {
        'chronic_disease_rate': 0.3,
        'multiple_diagnosis_rate': 0.4,
        'er_visit_rate': 0.1,
        'high_cost_ratio': 0.25,
        'denial_rate': 0.15,
        'service_line_complexity': 'medium',
        'charge_range': (100, 5000),
        'diagnosis_weights': {
            'chronic': 0.3,
            'acute': 0.4,
            'preventive': 0.3
        },
        'provider_types': {
            'emergency': 0.1,
            'specialist': 0.3,
            'primary': 0.6
        }
    }
}

# Diagnosis code pools by category
DIAGNOSIS_POOLS = {
    'chronic': [
        'E11.65',  # Type 2 diabetes with complications
        'I10',     # Essential hypertension
        'E78.5',   # Hyperlipidemia
        'J44.1',   # COPD with exacerbation
        'M54.5',   # Low back pain (chronic)
        'E11.9',   # Type 2 diabetes without complications
        'I25.10',  # Atherosclerotic heart disease
        'N18.6',   # End stage renal disease
        'G93.1',   # Anoxic brain damage
        'F32.9',   # Major depressive disorder
    ],
    'acute': [
        'J18.9',   # Pneumonia
        'K59.00',  # Constipation
        'R50.9',   # Fever
        'R06.02',  # Shortness of breath
        'R51',     # Headache
        'N39.0',   # Urinary tract infection
        'K21.9',   # GERD
        'M79.3',   # Panniculitis
    ],
    'preventive': [
        'Z00.00',  # Encounter for general exam
        'Z00.121', # Encounter for routine child health check
        'Z13.9',   # Screening for unspecified disorder
        'Z87.891', # Personal history of nicotine dependence
        'Z79.899', # Other long term drug therapy
    ]
}

# Procedure code pools by complexity
PROCEDURE_POOLS = {
    'high_complexity': [
        '99285',  # ER visit - high complexity
        '99255',  # Inpatient consultation - high complexity
        '99245',  # Office consultation - high complexity
        '36415',  # Routine venipuncture
        '93000',  # EKG
        '80053',  # Comprehensive metabolic panel
    ],
    'medium_complexity': [
        '99214',  # Office visit - moderate complexity
        '99213',  # Office visit - low complexity
        '99203',  # Office visit - new patient
        '99204',  # Office visit - new patient moderate
    ],
    'low_complexity': [
        '99212',  # Office visit - straightforward
        '99211',  # Office visit - minimal
        '99395',  # Preventive visit
        '99396',  # Preventive visit
    ]
}


def _generate_volume(profile, override=None):
    """
    Generate volume based on business size profile
    
    Args:
        profile: Profile dict with min, max, and distribution parameters
        override: Manual override value (if provided, use this instead)
    
    Returns:
        Integer volume
    """
    if override is not None:
        return int(override)
    
    dist_type = profile.get('distribution', 'uniform')
    min_val = profile['min']
    max_val = profile['max']
    
    if dist_type == 'uniform':
        volume = random.randint(min_val, max_val)
    elif dist_type == 'poisson':
        lambda_param = profile.get('lambda', (min_val + max_val) / 2)
        volume = int(np.random.poisson(lambda_param))
        volume = max(min_val, min(volume, max_val))  # Clamp to range
    elif dist_type == 'lognormal':
        mean = profile.get('mean', np.log((min_val + max_val) / 2))
        sigma = profile.get('sigma', 0.5)
        volume = int(np.random.lognormal(mean, sigma))
        volume = max(min_val, min(volume, max_val))  # Clamp to range
    else:
        # Default to uniform
        volume = random.randint(min_val, max_val)
    
    return int(volume)


# Risk profile configurations
RISK_PROFILES = {
    'high_risk': {
        'chronic_disease_rate': 0.7,  # 70% chronic diseases
        'multiple_diagnosis_rate': 0.6,  # 60% have multiple diagnoses
        'er_visit_rate': 0.3,  # 30% ER visits
        'high_cost_ratio': 0.5,  # 50% high-cost claims
        'denial_rate': 0.25,  # 25% denied
        'service_line_complexity': 'high',  # More service lines
        'charge_range': (500, 15000),  # Higher charge range
        'diagnosis_weights': {
            'chronic': 0.7,  # Chronic diseases (diabetes, heart disease, etc.)
            'acute': 0.2,
            'preventive': 0.1
        },
        'provider_types': {
            'emergency': 0.3,
            'specialist': 0.4,
            'primary': 0.3
        }
    },
    'low_risk': {
        'chronic_disease_rate': 0.1,  # 10% chronic diseases
        'multiple_diagnosis_rate': 0.2,  # 20% have multiple diagnoses
        'er_visit_rate': 0.02,  # 2% ER visits
        'high_cost_ratio': 0.1,  # 10% high-cost claims
        'denial_rate': 0.05,  # 5% denied
        'service_line_complexity': 'low',  # Fewer service lines
        'charge_range': (50, 500),  # Lower charge range
        'diagnosis_weights': {
            'chronic': 0.1,
            'acute': 0.3,
            'preventive': 0.6  # Mostly preventive
        },
        'provider_types': {
            'emergency': 0.02,
            'specialist': 0.2,
            'primary': 0.78
        }
    },
    'balanced': {
        'chronic_disease_rate': 0.3,
        'multiple_diagnosis_rate': 0.4,
        'er_visit_rate': 0.1,
        'high_cost_ratio': 0.25,
        'denial_rate': 0.15,
        'service_line_complexity': 'medium',
        'charge_range': (100, 5000),
        'diagnosis_weights': {
            'chronic': 0.3,
            'acute': 0.4,
            'preventive': 0.3
        },
        'provider_types': {
            'emergency': 0.1,
            'specialist': 0.3,
            'primary': 0.6
        }
    }
}

# Diagnosis code pools by category
DIAGNOSIS_POOLS = {
    'chronic': [
        {"code": "E11.65", "description": "Type 2 diabetes mellitus with hyperglycemia"},
        {"code": "I10", "description": "Essential (primary) hypertension"},
        {"code": "E78.5", "description": "Hyperlipidemia"},
        {"code": "J44.1", "description": "COPD with exacerbation"},
        {"code": "M54.5", "description": "Low back pain"},
        {"code": "E11.9", "description": "Type 2 diabetes without complications"},
        {"code": "I25.10", "description": "Atherosclerotic heart disease"},
        {"code": "N18.6", "description": "End stage renal disease"},
        {"code": "F32.9", "description": "Major depressive disorder"},
    ],
    'acute': [
        {"code": "J18.9", "description": "Pneumonia, unspecified"},
        {"code": "K59.00", "description": "Constipation"},
        {"code": "R50.9", "description": "Fever"},
        {"code": "R06.02", "description": "Shortness of breath"},
        {"code": "R51", "description": "Headache"},
        {"code": "N39.0", "description": "Urinary tract infection"},
        {"code": "K21.9", "description": "GERD"},
    ],
    'preventive': [
        {"code": "Z00.00", "description": "Encounter for general exam"},
        {"code": "Z00.121", "description": "Encounter for routine child health check"},
        {"code": "Z13.9", "description": "Screening for unspecified disorder"},
        {"code": "Z79.899", "description": "Other long term drug therapy"},
    ]
}

# Procedure code pools by complexity
PROCEDURE_POOLS = {
    'high_complexity': ["99285", "99255", "99245", "36415", "93000", "80053"],
    'medium_complexity': ["99214", "99213", "99203", "99204"],
    'low_complexity': ["99212", "99211", "99395", "99396"]
}

# Place of service codes
PLACE_OF_SERVICE = {
    'emergency': ["23"],  # ER
    'specialist': ["11", "22"],  # Office, Outpatient hospital
    'primary': ["11", "12"]  # Office, Home
}


def _select_diagnosis_codes(risk_config):
    """
    Select diagnosis codes based on risk profile
    
    Returns:
        List of diagnosis code dicts
    """
    weights = risk_config['diagnosis_weights']
    multiple_rate = risk_config['multiple_diagnosis_rate']
    
    # Select category based on weights
    category = random.choices(
        ['chronic', 'acute', 'preventive'],
        weights=[weights['chronic'], weights['acute'], weights['preventive']]
    )[0]
    
    # Determine number of diagnoses
    if random.random() < multiple_rate:
        num_diag = random.randint(2, 4)
    else:
        num_diag = 1
    
    # Select from appropriate pool
    pool = DIAGNOSIS_POOLS[category]
    selected = random.sample(pool, min(num_diag, len(pool)))
    
    # For multiple diagnoses, mix categories
    if num_diag > 1 and random.random() < 0.3:
        other_categories = [c for c in ['chronic', 'acute', 'preventive'] if c != category]
        if other_categories:
            other_category = random.choice(other_categories)
            other_pool = DIAGNOSIS_POOLS[other_category]
            if other_pool:
                additional = random.sample(other_pool, min(1, len(other_pool)))
                selected.extend(additional)
    
    return selected[:num_diag]


def _calculate_billed_amount(risk_config):
    """
    Calculate billed amount based on risk profile
    
    Returns:
        Float billed amount
    """
    charge_range = risk_config['charge_range']
    high_cost_ratio = risk_config.get('high_cost_ratio', 0.25)
    
    if random.random() < high_cost_ratio:
        # High-cost claim
        amount = random.uniform(charge_range[1] * 0.6, charge_range[1])
    else:
        # Normal cost claim
        amount = random.uniform(charge_range[0], charge_range[1] * 0.6)
    
    return round(amount, 2)


def _get_service_line_count(risk_config):
    """
    Get number of service lines based on complexity
    
    Returns:
        Integer number of service lines
    """
    complexity = risk_config.get('service_line_complexity', 'medium')
    
    if complexity == 'high':
        return random.randint(3, 8)
    elif complexity == 'low':
        return random.randint(1, 2)
    else:  # medium
        return random.randint(2, 5)


def _select_procedure_code(risk_config, is_er=False):
    """
    Select procedure code based on risk profile
    
    Returns:
        String procedure code
    """
    complexity = risk_config.get('service_line_complexity', 'medium')
    
    if is_er:
        return random.choice(["99281", "99282", "99283", "99284", "99285"])
    
    if complexity == 'high':
        pool = PROCEDURE_POOLS['high_complexity'] + PROCEDURE_POOLS['medium_complexity']
    elif complexity == 'low':
        pool = PROCEDURE_POOLS['low_complexity'] + PROCEDURE_POOLS['medium_complexity']
    else:  # medium
        pool = PROCEDURE_POOLS['medium_complexity']
    
    return random.choice(pool)


def _select_place_of_service(risk_config, is_er=False):
    """
    Select place of service based on risk profile
    
    Returns:
        String place of service code
    """
    if is_er:
        return "23"  # ER
    
    provider_types = risk_config['provider_types']
    provider_type = random.choices(
        ['emergency', 'specialist', 'primary'],
        weights=[provider_types['emergency'], provider_types['specialist'], provider_types['primary']]
    )[0]
    
    return random.choice(PLACE_OF_SERVICE[provider_type])


def _get_claim_status(risk_config):
    """
    Get claim status based on denial rate
    
    Returns:
        String claim status code
    """
    denial_rate = risk_config.get('denial_rate', 0.15)
    
    if random.random() < denial_rate:
        # Denied claims
        return random.choice(["19", "20", "21", "22"])
    else:
        # Paid/pending claims
        return random.choice(["1", "2", "3", "4"])


def _introduce_invalid_data_834(member, enrollment, invalid_rate):
    """
    Introduce invalid data issues for EDI 834 records
    
    Returns:
        tuple: (member, enrollment, is_invalid, issue_type)
    """
    if random.random() > invalid_rate:
        return member, enrollment, False, None
    
    issue_type = random.choice([
        'missing_dob',
        'invalid_effective_date',
        'start_after_end',
        'invalid_gender',
        'wrong_plan_id'
    ])
    
    is_invalid = True
    
    if issue_type == 'missing_dob':
        member.dob = None
    elif issue_type == 'invalid_effective_date':
        # Set effective date in the future
        enrollment.start_date = fake.date_between(start_date='today', end_date='+1y')
    elif issue_type == 'start_after_end':
        # Set start date after end date
        enrollment.start_date = fake.date_between(start_date='-1y', end_date='today')
        enrollment.end_date = enrollment.start_date - timedelta(days=random.randint(1, 365))
    elif issue_type == 'invalid_gender':
        # Invalid gender code
        member.gender = random.choice(['X', 'U', 'O', ''])
    elif issue_type == 'wrong_plan_id':
        # Non-existent plan ID
        member.plan = {"id": "INVALID-PLAN", "name": "Invalid Plan", "type": "INVALID"}
    
    return member, enrollment, is_invalid, issue_type


def _introduce_invalid_data_837(claim_data, service_lines, invalid_rate):
    """
    Introduce invalid data issues for EDI 837 records
    
    Returns:
        tuple: (claim_data, service_lines, is_invalid, issue_type)
    """
    if random.random() > invalid_rate:
        return claim_data, service_lines, False, None
    
    issue_type = random.choice([
        'charge_mismatch',
        'invalid_diagnosis',
        'future_service_date',
        'invalid_npi_length',
        'negative_amount'
    ])
    
    is_invalid = True
    
    if issue_type == 'charge_mismatch':
        # Make total charge less than sum of service lines
        if service_lines:
            total_lines = sum(float(line.get('billed_amount', 0)) for line in service_lines)
            claim_data['billed_amount'] = max(0, total_lines * random.uniform(0.5, 0.8))
    elif issue_type == 'invalid_diagnosis':
        # Add invalid diagnosis code
        claim_data['invalid_diagnosis'] = 'INVALID.999'
    elif issue_type == 'future_service_date':
        # Service date in the future
        if claim_data.get('service_date'):
            claim_data['service_date'] = fake.date_between(start_date='today', end_date='+1y')
    elif issue_type == 'invalid_npi_length':
        # NPI with wrong length (should be 10 digits)
        claim_data['invalid_npi'] = ''.join(random.choices(string.digits, k=random.choice([8, 9, 11, 12])))
    elif issue_type == 'negative_amount':
        # Negative billed amount
        claim_data['billed_amount'] = -abs(claim_data.get('billed_amount', 100))
    
    return claim_data, service_lines, is_invalid, issue_type


def _introduce_invalid_data_835(payment_data, invalid_rate):
    """
    Introduce invalid data issues for EDI 835 records
    
    Returns:
        tuple: (payment_data, is_invalid, issue_type)
    """
    if random.random() > invalid_rate:
        return payment_data, False, None
    
    issue_type = random.choice([
        'negative_payment',
        'mismatched_ids',
        'invalid_adjustment_code',
        'payment_exceeds_billed'
    ])
    
    is_invalid = True
    
    if issue_type == 'negative_payment':
        # Negative payment amount
        payment_data['paid_amount'] = -abs(payment_data.get('paid_amount', 100))
    elif issue_type == 'mismatched_ids':
        # Mismatched claim ID
        payment_data['claim_id'] = 'MISMATCHED-' + generate_id("", 10)
    elif issue_type == 'invalid_adjustment_code':
        # Invalid adjustment code
        payment_data['adjustment_code'] = 'INVALID'
    elif issue_type == 'payment_exceeds_billed':
        # Payment exceeds billed amount
        billed = payment_data.get('billed_amount', 100)
        payment_data['paid_amount'] = billed * random.uniform(1.1, 1.5)
    
    return payment_data, is_invalid, issue_type


def _write_csv(data_rows, headers, output_file):
    """Write data to CSV file"""
    # Create directory if output_file has a directory path
    dir_path = os.path.dirname(output_file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data_rows)


def generate_edi_834(num_members=None, output_file=None, format="x12", business_size="medium", invalid_rate=0.0):
    """
    Generate EDI 834 file (Enrollment) in X12 or CSV format
    
    Args:
        num_members: Number of members to generate (None = auto from business_size)
        output_file: Output file path
        format: Output format - "x12" or "csv"
        business_size: Business size profile - "small", "medium", or "large"
                       Determines volume range if num_members is None
        invalid_rate: Rate of invalid data (0.0-1.0). 0.05 = 5% invalid records
    
    Returns:
        Generated content as string (X12) or dict with metadata (CSV)
        CSV format returns: {
            "output_file": "...",
            "total_records": 1000,
            "invalid_records": 50,
            "invalid_rate": 0.05,
            "data": [...]
        }
    """
    # Generate volume based on business size if not specified
    if num_members is None:
        profile = BUSINESS_SIZE_PROFILES.get(business_size, BUSINESS_SIZE_PROFILES['medium'])
        num_members = _generate_volume(profile['834'])
        print(f"Auto-generated volume for {business_size} business: {num_members} members")
    
    if output_file is None:
        if format == "csv":
            output_file = os.path.join(SAMPLES_DIR, "edi_834_large_sample.csv")
        else:
            output_file = os.path.join(SAMPLES_DIR, "edi_834_large_sample.txt")
    
    if format == "csv":
        return _generate_edi_834_csv(num_members, output_file, invalid_rate)
    else:
        return _generate_edi_834_x12(num_members, output_file, invalid_rate)


def _generate_edi_834_x12(num_members=1000, output_file=None, invalid_rate=0.0):
    """Generate EDI 834 file in X12 format"""
    print(f"Generating EDI 834 data for {num_members} members...")
    if invalid_rate > 0:
        print(f"  Invalid data rate: {invalid_rate*100:.1f}%")

    segments = []
    current_date = datetime.now()

    # Generate ISA and GS segments, get ISA control number
    isa_gs_segments, isa_control_num = generate_isa_gs_segments("834", current_date)
    segments.extend(isa_gs_segments)

    # ST segment - use same version as GS segment (004010X095A1)
    st_index = len(segments)  # Track ST segment position for SE count
    segments.append("ST*834*0001*004010X095A1~")

    # BGN segment
    action_code = random.choice(["2", "4"])
    segments.append("BGN*00*{ref}*{date}*{time}**{action_code}~".format(
        ref="REF" + generate_id("", 9),
        date=current_date.strftime("%Y%m%d"),
        time=current_date.strftime("%H%M%S"),
        action_code=action_code
    ))

    # Add N1 segments (Sponsor and Payer information)
    segments.append("N1*P5*{}*FI*{}~".format("SPONSOR_NAME", generate_id("TAX", 9)))
    segments.append("N1*IN*{}*FI*{}~".format("PAYER_NAME", generate_id("TAX", 9)))

    # Generate members in batches
    for batch_start in range(0, num_members, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, num_members)
        print(f"Processing members {batch_start + 1} to {batch_end}...")

        batch_members = []
        for _ in range(batch_start, batch_end):
            member = Member()
            enrollment = Enrollment(member)
            batch_members.append(member)
            global_data['enrollments'][enrollment.id] = enrollment

        # Generate EDI segments for this batch
        for member in batch_members:
            coverage_status, termination_reason, end_date = member.status_info
            enrollment = next(e for e in global_data['enrollments'].values() if e.member_id == member.id)
            
            # Introduce invalid data if requested
            member, enrollment, is_invalid, issue_type = _introduce_invalid_data_834(
                member, enrollment, invalid_rate
            )

            # INS segment - Member insurance information
            medicare_plan = random.choice(['A', 'B', 'C', 'E']) if random.random() < 0.3 else None
            segments.append("INS*Y*18*030*{coverage_status}*{medicare_plan}***FT*Y~".format(
                coverage_status=coverage_status,
                medicare_plan=medicare_plan if medicare_plan else ''
            ))

            # REF segments - Member IDs
            segments.append("REF*0F*{member_id}~".format(member_id=member.id))
            segments.append("REF*38*{policy_num}~".format(policy_num=member.policy_num))
            segments.append("REF*SY*{ssn}~".format(ssn=member.ssn))

            # NM1 segment - Member name
            segments.append("NM1*IL*1*{last_name}*{first_name}***MI*{member_id}~".format(
                last_name=member.last_name,
                first_name=member.first_name,
                member_id=member.id
            ))

            # PER segment - Member contact
            segments.append("PER*IP**HP*{phone}*EM*{email}~".format(
                phone=member.phone,
                email=member.email
            ))

            # N3 and N4 segments - Member address
            segments.append("N3*{street}~".format(street=member.street))
            segments.append("N4*{city}*{state}*{zip}*{country}~".format(
                city=member.city,
                state=member.state,
                zip=member.zip_code,
                country="US"
            ))

            # DMG segment - Member demographics
            segments.append("DMG*D8*{dob}*{gender}~".format(
                dob=member.dob.strftime("%Y%m%d"),
                gender=member.gender
            ))

            # HD segment - Health plan
            segments.append("HD*030*HLT*{plan_type}*{plan_id}*{plan_name}~".format(
                plan_type=member.plan["type"],
                plan_id=member.plan["id"],
                plan_name=member.plan["name"]
            ))

            # DTP segment - Plan dates
            segments.append("DTP*356*D8*{start_date}~".format(
                start_date=enrollment.start_date.strftime("%Y%m%d")
            ))

            # For terminated members
            if coverage_status == 'T' and end_date:
                segments.append("DTP*357*D8*{end_date}~".format(
                    end_date=end_date.strftime("%Y%m%d")
                ))
                segments.append("INS***{termination_reason}~".format(termination_reason=termination_reason))

    # End segments
    # SE count: number of segments from ST (inclusive) to SE (inclusive)
    se_count = len(segments) - st_index + 1  # +1 to include SE itself
    segments.append("SE*{count}*0001~".format(count=se_count))
    segments.append("GE*1*1~")  # 1 transaction set in this functional group
    segments.append("IEA*1*{control_num}~".format(control_num=isa_control_num))

    # Write to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding='utf8') as f:
        f.write("\n".join(segments))

    print(f"Successfully generated EDI 834 data for {num_members} members in {output_file}")
    return "\n".join(segments)


def _generate_edi_834_csv(num_members=1000, output_file=None, invalid_rate=0.0):
    """Generate EDI 834 data in CSV format"""
    print(f"Generating EDI 834 CSV data for {num_members} members...")
    if invalid_rate > 0:
        print(f"  Invalid data rate: {invalid_rate*100:.1f}%")
    
    # CSV Schema for 834
    headers = [
        'member_id', 'subscriber_id', 'policy_number', 'ssn',
        'last_name', 'first_name', 'middle_initial',
        'date_of_birth', 'gender',
        'street_address', 'city', 'state', 'zip_code', 'country',
        'phone', 'email',
        'coverage_status', 'medicare_plan',
        'plan_id', 'plan_name', 'plan_type',
        'effective_date', 'termination_date', 'termination_reason',
        'relationship_code', 'transaction_type', 'action_code',
        'sponsor_id', 'insurance_line'
    ]
    
    csv_rows = []
    invalid_count = 0
    current_date = datetime.now()
    
    # Generate members in batches
    for batch_start in range(0, num_members, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, num_members)
        print(f"Processing members {batch_start + 1} to {batch_end}...")
        
        batch_members = []
        for _ in range(batch_start, batch_end):
            member = Member()
            enrollment = Enrollment(member)
            batch_members.append((member, enrollment))
            global_data['enrollments'][enrollment.id] = enrollment
        
        # Generate CSV rows for this batch
        for member, enrollment in batch_members:
            # Introduce invalid data if requested
            member, enrollment, is_invalid, issue_type = _introduce_invalid_data_834(
                member, enrollment, invalid_rate
            )
            if is_invalid:
                invalid_count += 1
            
            coverage_status, termination_reason, end_date = member.status_info
            medicare_plan = random.choice(['A', 'B', 'C', 'E']) if random.random() < 0.3 else None
            
            row = {
                'member_id': member.id,
                'subscriber_id': member.id,  # Self subscriber
                'policy_number': member.policy_num,
                'ssn': member.ssn,
                'last_name': member.last_name,
                'first_name': member.first_name,
                'middle_initial': '',
                'date_of_birth': member.dob.strftime("%Y-%m-%d") if member.dob else '',
                'gender': member.gender,
                'street_address': member.street,
                'city': member.city,
                'state': member.state,
                'zip_code': member.zip_code,
                'country': 'US',
                'phone': member.phone,
                'email': member.email,
                'coverage_status': coverage_status,
                'medicare_plan': medicare_plan if medicare_plan else '',
                'plan_id': member.plan["id"],
                'plan_name': member.plan["name"],
                'plan_type': member.plan["type"],
                'effective_date': enrollment.start_date.strftime("%Y-%m-%d") if enrollment.start_date else '',
                'termination_date': end_date.strftime("%Y-%m-%d") if end_date else '',
                'termination_reason': termination_reason if termination_reason else '',
                'relationship_code': enrollment.relationship_code,
                'transaction_type': enrollment.transaction_type,
                'action_code': enrollment.action_code,
                'sponsor_id': enrollment.sponsor_id,
                'insurance_line': enrollment.insurance_line
            }
            csv_rows.append(row)
    
    # Write CSV file
    _write_csv(csv_rows, headers, output_file)
    # Calculate actual invalid rate
    actual_invalid_rate = invalid_count / len(csv_rows) if csv_rows else 0.0
    
    print(f"Successfully generated EDI 834 CSV data for {num_members} members in {output_file}")
    print(f"  Total records: {len(csv_rows)}, Invalid records: {invalid_count}, Invalid rate: {actual_invalid_rate:.3f}")
    
    return {
        "output_file": output_file,
        "total_records": len(csv_rows),
        "invalid_records": invalid_count,
        "invalid_rate": actual_invalid_rate,
        "data": csv_rows
    }


def generate_edi_837(num_claims=None, claims_per_member=None, output_file=None, format="x12", business_size="medium", invalid_rate=0.0, risk_profile="balanced", custom_distribution=None):
    """
    Generate EDI 837 file (Claims) in X12 or CSV format
    
    Args:
        num_claims: Number of claims to generate (None = auto from business_size)
        claims_per_member: Claims per member if num_claims is None (None = auto-calculate)
        output_file: Output file path
        format: Output format - "x12" or "csv"
        business_size: Business size profile - "small", "medium", or "large"
                       Determines volume range if num_claims is None
        invalid_rate: Rate of invalid data (0.0-1.0). 0.05 = 5% invalid records
        risk_profile: Risk profile - "high_risk", "low_risk", or "balanced"
        custom_distribution: Dict with custom distribution parameters to override risk_profile
                           e.g., {"high_cost_ratio": 0.3, "denial_rate": 0.15, "er_visit_rate": 0.1}
    
    Returns:
        Generated content as string (X12) or dict with metadata (CSV)
        CSV format returns: {
            "output_file": "...",
            "total_records": 1000,
            "invalid_records": 50,
            "invalid_rate": 0.05,
            "data": [...]
        }
    """
    # Generate volume based on business size if not specified
    if num_claims is None:
        profile = BUSINESS_SIZE_PROFILES.get(business_size, BUSINESS_SIZE_PROFILES['medium'])
        num_claims = _generate_volume(profile['837'])
        print(f"Auto-generated volume for {business_size} business: {num_claims} claims")
    elif claims_per_member is None:
        # If num_claims is specified but claims_per_member is not, use default
        claims_per_member = 3
    
    if output_file is None:
        if format == "csv":
            output_file = os.path.join(SAMPLES_DIR, "edi_837_large_sample.csv")
        else:
            output_file = os.path.join(SAMPLES_DIR, "edi_837_large_sample.txt")
    
    # Merge risk profile with custom distribution
    if custom_distribution:
        base_profile = RISK_PROFILES.get(risk_profile, RISK_PROFILES['balanced']).copy()
        base_profile.update(custom_distribution)
        risk_config = base_profile
    else:
        risk_config = RISK_PROFILES.get(risk_profile, RISK_PROFILES['balanced']).copy()
    
    # Add profile name for logging
    risk_config['_profile_name'] = risk_profile
    
    if format == "csv":
        return _generate_edi_837_csv(num_claims, claims_per_member, output_file, invalid_rate, risk_config)
    else:
        return _generate_edi_837_x12(num_claims, claims_per_member, output_file, invalid_rate, risk_config)


def _generate_edi_837_x12(num_claims=None, claims_per_member=3, output_file=None, invalid_rate=0.0, risk_config=None):
    """Generate EDI 837 file in X12 format"""
    if risk_config is None:
        risk_config = RISK_PROFILES['balanced']
    
    if invalid_rate > 0:
        print(f"  Invalid data rate: {invalid_rate*100:.1f}%")
    print(f"  Risk profile: {risk_config.get('_profile_name', 'custom')}")
    if not global_data['members']:
        print("No members found. Generating sample members first...")
        _generate_edi_834_x12(1000, os.path.join(SAMPLES_DIR, "temp_834.txt"), 0.0)

    if not global_data['providers']:
        print("Generating providers...")
        for _ in range(100):  # Generate 100 providers
            Provider()

    members = list(global_data['members'].values())
    providers = list(global_data['providers'].values())

    # Calculate number of claims if not specified
    if num_claims is None:
        num_claims = len(members) * claims_per_member

    segments = []
    current_date = datetime.now()

    # Generate ISA and GS segments, get ISA control number
    isa_gs_segments, isa_control_num = generate_isa_gs_segments("837", current_date)
    segments.extend(isa_gs_segments)

    # ST segment
    st_index = len(segments)  # Track ST segment position for SE count
    segments.append("ST*837*0001*004010X098A1~")

    # BHT segment
    segments.append("BHT*0019*00*{ref}*{date}*{time}*CH~".format(
        ref="REF" + generate_id("", 9),
        date=current_date.strftime("%Y%m%d"),
        time=current_date.strftime("%H%M%S")
    ))

    # Submitter and receiver info
    segments.append("NM1*41*2*PROVIDER BILLING*****46*{provider_id}~".format(
        provider_id=providers[0].id
    ))
    segments.append("NM1*40*2*INSURANCE COMPANY*****46*PAYER123~")

    print(f"Generating {num_claims} claims...")

    # Generate claims in batches
    for i in range(num_claims):
        if i > 0 and i % 100 == 0:
            print(f"Generated {i} claims so far...")

        claim_id = generate_id("CLM" + current_date.strftime("%Y"), 6)
        provider = random.choice(providers)
        member = random.choice(members)

        # Get or create enrollment
        enrollment = next((e for e in global_data['enrollments'].values() if e.member_id == member.id), None)
        if not enrollment:
            enrollment = Enrollment(member)

        # Store claim data
        claim_data = {
            'id': claim_id,
            'member_id': member.id,
            'provider_id': provider.id,
            'enrollment_id': enrollment.id,
            'service_date': None,
            'billed_amount': 0,
            'paid_amount': 0
        }
        global_data['claims'][claim_id] = claim_data

        # HL segment - Claim hierarchy
        segments.append("HL*{level}*{parent}*22*1~".format(
            level=i + 1,
            parent=i if i > 0 else ""
        ))

        # PRV segment - Provider type
        segments.append("PRV*BI*PXC*{taxonomy}~".format(
            taxonomy=provider.taxonomy
        ))

        # NM1 segment - Provider info
        segments.append("NM1*85*2*{last_name}*{first_name}***XX*{npi}~".format(
            last_name=provider.last_name,
            first_name=provider.first_name,
            npi=provider.npi
        ))

        # REF segment - Provider secondary ID
        segments.append("REF*EI*{tax_id}~".format(tax_id=provider.tax_id))

        # N3 and N4 segments - Provider address
        segments.append("N3*{street}~".format(street=provider.street))
        segments.append("N4*{city}*{state}*{zip}~".format(
            city=provider.city,
            state=provider.state,
            zip=provider.zip
        ))

        # NM1 segment - Member info
        segments.append("NM1*IL*1*{last_name}*{first_name}***MI*{member_id}~".format(
            last_name=member.last_name,
            first_name=member.first_name,
            member_id=member.id
        ))

        # DMG segment - Member demographics
        segments.append("DMG*D8*{dob}*{gender}~".format(
            dob=member.dob.strftime("%Y%m%d"),
            gender=member.gender
        ))

        # Determine if ER visit based on risk profile
        is_er = random.random() < risk_config.get('er_visit_rate', 0.1)

        # CLM segment - Claim info
        billed_amount = _calculate_billed_amount(risk_config)
        claim_status = _get_claim_status(risk_config)
        segments.append("CLM*{claim_id}*{billed_amount}***{service_type}:{modifier}*Y*A*Y*Y~".format(
            claim_id=claim_id,
            billed_amount=billed_amount,
            service_type=random.choice(["A", "B", "C"]),
            modifier=random.choice(["", "25", "59", "76"])
        ))
        claim_data['billed_amount'] = billed_amount

        # DTP segment - Service date
        if enrollment.end_date:
            # Ensure end_date is after start_date
            if enrollment.end_date > enrollment.start_date:
                max_date = min(datetime.now().date(), enrollment.end_date)
            else:
                max_date = datetime.now().date()
        else:
            max_date = datetime.now().date()

        # Ensure start_date is before max_date
        if enrollment.start_date < max_date:
            service_date = fake.date_between(
                start_date=enrollment.start_date,
                end_date=max_date
            )
        else:
            # If dates are invalid, use current date
            service_date = datetime.now().date()

        segments.append("DTP*472*D8*{service_date}~".format(
            service_date=service_date.strftime("%Y%m%d")
        ))
        claim_data['service_date'] = service_date

        # Diagnosis codes based on risk profile
        diag_codes = _select_diagnosis_codes(risk_config)
        
        for diag in diag_codes:
            segments.append(f"HI*ABK:{diag['code']}~")

        # Service line items based on risk profile
        line_amounts = []
        remaining_amount = billed_amount
        num_lines = _get_service_line_count(risk_config)
        
        for line_num in range(1, num_lines + 1):
            if line_num == num_lines:
                line_amount = round(remaining_amount, 2)
            else:
                line_amount = round(remaining_amount * random.uniform(0.2, 0.4), 2)
            remaining_amount -= line_amount
            line_amounts.append(line_amount)

            procedure_code = _select_procedure_code(risk_config, is_er)
            modifier = random.choice(["", "25", "59", "76"])
            place_of_service = _select_place_of_service(risk_config, is_er)

            segments.append(f"LX*{line_num}~")
            segments.append(f"SV1*HC:{procedure_code}{':' + modifier if modifier else ''}*{line_amount}*UN*1***1~")
            segments.append(f"REF*6R*{place_of_service}~")
            segments.append(f"DTP*472*D8*{service_date.strftime('%Y%m%d')}~")

    # End segments
    # SE count: number of segments from ST (inclusive) to SE (inclusive)
    se_count = len(segments) - st_index + 1  # +1 to include SE itself
    segments.append("SE*{count}*0001~".format(count=se_count))
    segments.append("GE*1*1~")  # 1 transaction set in this functional group
    segments.append("IEA*1*{control_num}~".format(control_num=isa_control_num))

    # Write to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding='utf8') as f:
        f.write("\n".join(segments))

    print(f"Successfully generated EDI 837 data with {num_claims} claims in {output_file}")
    return "\n".join(segments)


def _generate_edi_837_csv(num_claims=None, claims_per_member=3, output_file=None, invalid_rate=0.0, risk_config=None):
    """Generate EDI 837 data in CSV format"""
    if risk_config is None:
        risk_config = RISK_PROFILES['balanced']
    
    if not global_data['members']:
        print("No members found. Generating sample members first...")
        _generate_edi_834_x12(1000, os.path.join(SAMPLES_DIR, "temp_834.txt"), 0.0)
    
    if not global_data['providers']:
        print("Generating providers...")
        for _ in range(100):
            Provider()
    
    members = list(global_data['members'].values())
    providers = list(global_data['providers'].values())
    
    if num_claims is None:
        num_claims = len(members) * claims_per_member
    
    if invalid_rate > 0:
        print(f"  Invalid data rate: {invalid_rate*100:.1f}%")
    print(f"  Risk profile: {risk_config.get('_profile_name', 'custom')}")
    
    # CSV Schema for 837
    headers = [
        'claim_id', 'member_id', 'provider_id', 'provider_npi', 'provider_tax_id',
        'provider_last_name', 'provider_first_name', 'provider_specialty',
        'provider_street', 'provider_city', 'provider_state', 'provider_zip',
        'member_last_name', 'member_first_name',
        'member_dob', 'member_gender',
        'service_date', 'billed_amount', 'claim_status', 'claim_frequency_code',
        'claim_source_code', 'facility_type_code', 'location_type',
        'procedure_code', 'procedure_description', 'diagnosis_codes',
        'submission_date', 'enrollment_id'
    ]
    
    csv_rows = []
    invalid_count = 0
    current_date = datetime.now()
    
    print(f"Generating {num_claims} claims...")
    
    for i in range(num_claims):
        if i > 0 and i % 100 == 0:
            print(f"Generated {i} claims so far...")
        
        claim_id = generate_id("CLM" + current_date.strftime("%Y"), 6)
        provider = random.choice(providers)
        member = random.choice(members)
        
        enrollment = next((e for e in global_data['enrollments'].values() if e.member_id == member.id), None)
        if not enrollment:
            enrollment = Enrollment(member)
        
        # Calculate service date
        if enrollment.end_date:
            max_date = min(datetime.now().date(), enrollment.end_date) if enrollment.end_date > enrollment.start_date else datetime.now().date()
        else:
            max_date = datetime.now().date()
        
        if enrollment.start_date < max_date:
            service_date = fake.date_between(start_date=enrollment.start_date, end_date=max_date)
        else:
            service_date = datetime.now().date()
        
        # Determine if ER visit based on risk profile
        is_er = random.random() < risk_config.get('er_visit_rate', 0.1)
        
        billed_amount = _calculate_billed_amount(risk_config)
        claim_status = _get_claim_status(risk_config)
        
        # Get diagnosis codes based on risk profile
        diag_code_objects = _select_diagnosis_codes(risk_config)
        diag_codes = [d['code'] for d in diag_code_objects]
        
        # Get procedure code and place of service based on risk profile
        procedure_code = _select_procedure_code(risk_config, is_er)
        place_of_service = _select_place_of_service(risk_config, is_er)
        procedure_map = {
            '99213': 'Office/outpatient visit est',
            '99214': 'Office/outpatient visit est',
            '99203': 'Office/outpatient visit new',
            '99204': 'Office/outpatient visit new',
            '99215': 'Office/outpatient visit est',
            '99244': 'Office consult'
        }
        
        # Service lines for charge mismatch check
        service_lines = [{'billed_amount': billed_amount * 0.6}, {'billed_amount': billed_amount * 0.4}]
        
        claim_data = {
            'id': claim_id,
            'member_id': member.id,
            'provider_id': provider.id,
            'enrollment_id': enrollment.id,
            'service_date': service_date,
            'billed_amount': billed_amount,
            'paid_amount': 0
        }
        
        # Introduce invalid data if requested
        claim_data, service_lines, is_invalid, issue_type = _introduce_invalid_data_837(
            claim_data, service_lines, invalid_rate
        )
        if is_invalid:
            invalid_count += 1
        
        global_data['claims'][claim_id] = claim_data
        
        # Handle invalid diagnosis codes
        if 'invalid_diagnosis' in claim_data:
            diag_codes.append(claim_data['invalid_diagnosis'])
        
        # Handle invalid NPI
        provider_npi = provider.npi
        if 'invalid_npi' in claim_data:
            provider_npi = claim_data['invalid_npi']
        
        row = {
            'claim_id': claim_id,
            'member_id': member.id,
            'provider_id': provider.id,
            'provider_npi': provider_npi,
            'provider_tax_id': provider.tax_id,
            'provider_last_name': provider.last_name,
            'provider_first_name': provider.first_name,
            'provider_specialty': provider.specialty,
            'provider_street': provider.street,
            'provider_city': provider.city,
            'provider_state': provider.state,
            'provider_zip': provider.zip,
            'member_last_name': member.last_name,
            'member_first_name': member.first_name,
            'member_dob': member.dob.strftime("%Y-%m-%d"),
            'member_gender': member.gender,
            'service_date': claim_data['service_date'].strftime("%Y-%m-%d") if isinstance(claim_data['service_date'], datetime) or hasattr(claim_data['service_date'], 'strftime') else str(claim_data.get('service_date', service_date)),
            'billed_amount': f"{claim_data['billed_amount']:.2f}",
            'claim_status': claim_status,
            'claim_frequency_code': '1',
            'claim_source_code': '01',
            'facility_type_code': place_of_service,
            'location_type': 'ER' if is_er or place_of_service == '23' else ('OFFICE' if place_of_service == '11' else 'OUTPATIENT'),
            'procedure_code': procedure_code,
            'procedure_description': procedure_map.get(procedure_code, 'Medical service'),
            'diagnosis_codes': '|'.join(diag_codes),
            'submission_date': current_date.strftime("%Y-%m-%d"),
            'enrollment_id': enrollment.id
        }
        csv_rows.append(row)
    
    _write_csv(csv_rows, headers, output_file)
    
    # Calculate actual invalid rate
    actual_invalid_rate = invalid_count / len(csv_rows) if csv_rows else 0.0
    
    print(f"Successfully generated EDI 837 CSV data with {num_claims} claims in {output_file}")
    print(f"  Total records: {len(csv_rows)}, Invalid records: {invalid_count}, Invalid rate: {actual_invalid_rate:.3f}")
    
    return {
        "output_file": output_file,
        "total_records": len(csv_rows),
        "invalid_records": invalid_count,
        "invalid_rate": actual_invalid_rate,
        "data": csv_rows
    }


def generate_edi_835(num_payments=None, output_file=None, format="x12", business_size="medium", invalid_rate=0.0):
    """
    Generate EDI 835 file (Payment/Remittance) in X12 or CSV format
    
    Args:
        num_payments: Number of payments to generate (None = auto from business_size and claims)
        output_file: Output file path
        format: Output format - "x12" or "csv"
        business_size: Business size profile - "small", "medium", or "large"
                       Used if num_payments is None and no claims exist
        invalid_rate: Rate of invalid data (0.0-1.0). 0.05 = 5% invalid records
    
    Returns:
        Generated content as string (X12) or dict with metadata (CSV)
        CSV format returns: {
            "output_file": "...",
            "total_records": 1000,
            "invalid_records": 50,
            "invalid_rate": 0.05,
            "data": [...]
        }
    """
    # Generate volume based on business size if not specified
    if num_payments is None:
        # If claims exist, use 60% of claims as payments
        if global_data.get('claims'):
            total_claims = len(global_data['claims'])
            profile = BUSINESS_SIZE_PROFILES.get(business_size, BUSINESS_SIZE_PROFILES['medium'])
            paid_ratio = profile['835_ratio']['paid']
            num_payments = int(total_claims * paid_ratio)
            print(f"Auto-generated {num_payments} payments ({paid_ratio*100:.0f}% of {total_claims} claims)")
        else:
            # No claims exist, generate based on business size
            profile = BUSINESS_SIZE_PROFILES.get(business_size, BUSINESS_SIZE_PROFILES['medium'])
            # Use 60% of typical claim volume
            claim_volume = _generate_volume(profile['837'])
            num_payments = int(claim_volume * profile['835_ratio']['paid'])
            print(f"Auto-generated volume for {business_size} business: {num_payments} payments")
    
    if output_file is None:
        if format == "csv":
            output_file = os.path.join(SAMPLES_DIR, "edi_835_large_sample.csv")
        else:
            output_file = os.path.join(SAMPLES_DIR, "edi_835_large_sample.txt")
    
    if format == "csv":
        return _generate_edi_835_csv(num_payments, output_file, invalid_rate)
    else:
        return _generate_edi_835_x12(num_payments, output_file, invalid_rate)


def _generate_edi_835_x12(num_payments=500, output_file=None, invalid_rate=0.0):
    """Generate EDI 835 file in X12 format"""
    if invalid_rate > 0:
        print(f"  Invalid data rate: {invalid_rate*100:.1f}%")
    segments = []
    current_date = datetime.now()

    # If no claims exist, generate some first
    if not global_data['claims']:
        print("No claims found. Generating sample claims first...")
        _generate_edi_837_x12()

    claims = list(global_data['claims'].values())
    if len(claims) < num_payments:
        num_payments = len(claims)

    # Select random claims for payment
    paid_claims = random.sample(claims, num_payments)

    # Generate ISA and GS segments, get ISA control number
    isa_gs_segments, isa_control_num = generate_isa_gs_segments("835", current_date)
    segments.extend(isa_gs_segments)

    # ST segment
    st_index = len(segments)  # Track ST segment position for SE count
    segments.append("ST*835*0001*004010X091A1~")

    # Calculate total payment amount
    total_amount = round(sum(c['billed_amount'] * random.uniform(0.5, 0.9) for c in paid_claims), 2)

    # BPR segment - Financial information
    segments.append("BPR*I*{total_amount}*C*ACH*CC*01*{check_num}**DA*{account_num}*{routing_num}*{date}~".format(
        total_amount=total_amount,
        check_num=generate_id("CHK", 6),
        account_num=''.join(random.choices(string.digits, k=10)),
        routing_num=''.join(random.choices(string.digits, k=9)),
        date=current_date.strftime("%Y%m%d")
    ))

    # TRN segment - Transaction reference
    segments.append("TRN*1*{ref}*{payer_id}~".format(
        ref=generate_id("REF", 9),
        payer_id=generate_id("PAYER", 6)
    ))

    # Payer information
    segments.append("N1*PR*{}*FI*{}~".format(
        "PAYER_NAME",
        generate_id("TAX", 9)
    ))

    # Generate payment data
    for i, claim_data in enumerate(paid_claims):
        claim_id = claim_data['id']
        member = global_data['members'][claim_data['member_id']]
        provider = global_data['providers'][claim_data['provider_id']]

        # Calculate payment amounts
        paid_amount = round(claim_data['billed_amount'] * random.uniform(0.5, 0.9), 2)
        patient_responsibility = round(claim_data['billed_amount'] * random.uniform(0.1, 0.3), 2)
        allowed_amount = round(paid_amount + patient_responsibility, 2)

        # Update claim data
        claim_data['paid_amount'] = paid_amount
        claim_data['allowed_amount'] = allowed_amount

        # LX segment - Payment hierarchy
        segments.append("LX*{level}~".format(level=i + 1))

        # CLP segment - Claim payment info
        claim_status = random.choice(["1", "2", "3", "4", "19", "20", "21", "22"])
        claim_code = random.choice(["1", "2", "3", "A", "B", "C"])
        segments.append(
            "CLP*{claim_id}*{claim_status}*{billed_amount}*{paid_amount}*{patient_responsibility}*{claim_code}~".format(
                claim_id=claim_id,
                claim_status=claim_status,
                billed_amount=claim_data['billed_amount'],
                paid_amount=paid_amount,
                patient_responsibility=patient_responsibility,
                claim_code=claim_code
            ))

        # CAS segment - Adjustments (50% chance)
        if random.random() < 0.5:
            adjust_amount = round(paid_amount * random.uniform(0.05, 0.15), 2)
            adjust_code = random.choice(["CO", "OA", "PI", "PR"])
            segments.append("CAS*{adjust_code}*45*{adjust_amount}~".format(
                adjust_code=adjust_code,
                adjust_amount=adjust_amount
            ))

        # NM1 segment - Provider info
        segments.append("NM1*82*1*{last_name}*{first_name}***XX*{npi}~".format(
            last_name=provider.last_name,
            first_name=provider.first_name,
            npi=provider.npi
        ))

        # NM1 segment - Member info
        segments.append("NM1*IL*1*{last_name}*{first_name}***MI*{member_id}~".format(
            last_name=member.last_name,
            first_name=member.first_name,
            member_id=member.id
        ))

        # SVC segment - Service payment details
        procedure_code = random.choice(["99213", "99214", "99203", "99204"])
        segments.append("SVC*HC:{procedure_code}*{billed_amount}*{paid_amount}*{allowed_amount}~".format(
            procedure_code=procedure_code,
            billed_amount=claim_data['billed_amount'],
            paid_amount=paid_amount,
            allowed_amount=allowed_amount
        ))

        # DTM segments - Service and adjudication dates
        segments.append("DTM*150*D8*{service_date}~".format(
            service_date=claim_data['service_date'].strftime("%Y%m%d")
        ))
        segments.append("DTM*405*D8*{date}~".format(
            date=current_date.strftime("%Y%m%d")
        ))

    # PLB segment - Provider balance info (30% chance)
    if random.random() < 0.3:
        provider = random.choice(list(global_data['providers'].values()))
        segments.append("PLB*{provider_id}*{date}*CV:45*{amount}~".format(
            provider_id=provider.id,
            date=current_date.strftime("%Y%m%d"),
            amount=round(random.uniform(100, 500), 2)
        ))

    # End segments
    # SE count: number of segments from ST (inclusive) to SE (inclusive)
    se_count = len(segments) - st_index + 1  # +1 to include SE itself
    segments.append("SE*{count}*0001~".format(count=se_count))
    segments.append("GE*1*1~")  # 1 transaction set in this functional group
    segments.append("IEA*1*{control_num}~".format(control_num=isa_control_num))

    # Write to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding='utf8') as f:
        f.write("\n".join(segments))

    print(f"Successfully generated EDI 835 data with {num_payments} payments in {output_file}")
    return "\n".join(segments)


def _generate_edi_835_csv(num_payments=500, output_file=None, invalid_rate=0.0):
    """Generate EDI 835 data in CSV format"""
    if not global_data['claims']:
        print("No claims found. Generating sample claims first...")
        _generate_edi_837_x12(None, 3, os.path.join(SAMPLES_DIR, "temp_837.txt"))
    
    claims = list(global_data['claims'].values())
    if len(claims) < num_payments:
        num_payments = len(claims)
    
    paid_claims = random.sample(claims, num_payments)
    current_date = datetime.now()
    
    # CSV Schema for 835
    headers = [
        'payment_id', 'claim_id', 'member_id', 'provider_id', 'provider_npi',
        'member_last_name', 'member_first_name',
        'billed_amount', 'paid_amount', 'allowed_amount', 'patient_responsibility',
        'claim_status', 'claim_code', 'adjustment_code', 'adjustment_amount',
        'procedure_code', 'service_date', 'adjudication_date',
        'check_number', 'payment_date', 'payment_method',
        'payer_id', 'transaction_reference'
    ]
    
    csv_rows = []
    invalid_count = 0
    
    for i, claim_data in enumerate(paid_claims):
        claim_id = claim_data['id']
        member = global_data['members'][claim_data['member_id']]
        provider = global_data['providers'][claim_data['provider_id']]
        
        paid_amount = round(claim_data['billed_amount'] * random.uniform(0.5, 0.9), 2)
        patient_responsibility = round(claim_data['billed_amount'] * random.uniform(0.1, 0.3), 2)
        allowed_amount = round(paid_amount + patient_responsibility, 2)
        
        claim_status = random.choice(["1", "2", "3", "4", "19", "20", "21", "22"])
        claim_code = random.choice(["1", "2", "3", "A", "B", "C"])
        
        # Adjustment (50% chance)
        adjustment_code = ''
        adjustment_amount = ''
        if random.random() < 0.5:
            adjustment_code = random.choice(["CO", "OA", "PI", "PR"])
            adjustment_amount = f"{round(paid_amount * random.uniform(0.05, 0.15), 2):.2f}"
        
        procedure_code = random.choice(["99213", "99214", "99203", "99204"])
        payment_id = f"PAY{current_date.strftime('%Y%m%d%H%M%S%f')[:-3]}{i}"
        
        row = {
            'payment_id': payment_id,
            'claim_id': claim_id,
            'member_id': member.id,
            'provider_id': provider.id,
            'provider_npi': provider.npi,
            'member_last_name': member.last_name,
            'member_first_name': member.first_name,
            'billed_amount': f"{claim_data['billed_amount']:.2f}",
            'paid_amount': f"{paid_amount:.2f}",
            'allowed_amount': f"{allowed_amount:.2f}",
            'patient_responsibility': f"{patient_responsibility:.2f}",
            'claim_status': claim_status,
            'claim_code': claim_code,
            'adjustment_code': adjustment_code,
            'adjustment_amount': adjustment_amount,
            'procedure_code': procedure_code,
            'service_date': claim_data['service_date'].strftime("%Y-%m-%d") if claim_data.get('service_date') else '',
            'adjudication_date': current_date.strftime("%Y-%m-%d"),
            'check_number': generate_id("CHK", 6),
            'payment_date': current_date.strftime("%Y-%m-%d"),
            'payment_method': 'ACH',
            'payer_id': generate_id("PAYER", 6),
            'transaction_reference': generate_id("REF", 9)
        }
        csv_rows.append(row)
    
    _write_csv(csv_rows, headers, output_file)
    
    # Calculate actual invalid rate
    actual_invalid_rate = invalid_count / len(csv_rows) if csv_rows else 0.0
    
    print(f"Successfully generated EDI 835 CSV data with {num_payments} payments in {output_file}")
    print(f"  Total records: {len(csv_rows)}, Invalid records: {invalid_count}, Invalid rate: {actual_invalid_rate:.3f}")
    
    return {
        "output_file": output_file,
        "total_records": len(csv_rows),
        "invalid_records": invalid_count,
        "invalid_rate": actual_invalid_rate,
        "data": csv_rows
    }


def generate_edi_files(format="x12", business_size="medium"):
    """
    Generate all EDI files with datasets based on business size
    
    Args:
        format: Output format - "x12" or "csv"
        business_size: Business size profile - "small", "medium", or "large"
    """
    # Generate EDI 834
    generate_edi_834(business_size=business_size, format=format)

    # Generate EDI 837 (will auto-calculate based on business size)
    generate_edi_837(business_size=business_size, format=format)

    # Generate EDI 835 payments (will auto-calculate based on claims)
    generate_edi_835(business_size=business_size, format=format)

    print(f"Generated EDI 834, 837 and 835 sample files in {format.upper()} format for {business_size} business.")


if __name__ == "__main__":
    generate_edi_files()