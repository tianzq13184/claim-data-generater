import random
import string
import json
from datetime import datetime, timedelta
import pymysql
from faker import Faker
import mysql.connector
from mysql.connector import Error
# Initialize Faker for realistic data generation
fake = Faker()

# Database connection configuration
# DB_CONFIG = {
#     'host': 'insurance.cpy2e6qoaeck.ap-southeast-2.rds.amazonaws.com',
#     'database': 'insurance',
#     'user': 'root',
#     'password': 'Insurance_2025'
# }
DB_CONFIG = {
    'host': '192.168.10.20',
    'database': 'insurance',
    'user': 'root',
    'password': '123456'
}

def generate_random_id(prefix, length=8):
    """Generate a random ID with given prefix and length"""
    # suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    timestamp_part = datetime.now().strftime("%H%M%S%f")[:6]
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    # candidate_id = f"{prefix}{timestamp_part}{random_part}"
    return f"{prefix}{timestamp_part}{random_part}"
    # return f"{prefix}{suffix}"


def generate_address():
    """Generate a realistic address in JSON format"""
    return {
        "street": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip": fake.zipcode()
    }


def generate_fhir_resource(member_id, resource_type):
    """Generate a basic FHIR resource"""
    if resource_type == "Patient":
        resource = {
            "resourceType": "Patient",
            "id": member_id,
            "name": [{"family": fake.last_name(), "given": [fake.first_name()]}],
            "birthDate": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
            "gender": random.choice(["male", "female"]),
            "address": [{
                "line": [fake.street_address()],
                "city": fake.city(),
                "state": fake.state_abbr(),
                "postalCode": fake.zipcode()
            }]
        }
    elif resource_type == "Observation":
        resource = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": random.choice(["29463-7", "3141-9", "39156-5"]),
                    "display": random.choice(["Body weight", "Body mass index", "Blood pressure"])
                }]
            },
            "subject": {"reference": f"Patient/{member_id}"},
            "effectiveDateTime": fake.date_time_this_year().isoformat(),
            "valueQuantity": {
                "value": round(random.uniform(50, 200), 2),
                "unit": random.choice(["kg", "cm", "mmHg"])
            }
        }
    else:
        resource = {
            "resourceType": resource_type,
            "id": member_id + "-" + resource_type.lower(),
            "meta": {"lastUpdated": datetime.now().isoformat()}
        }

    return json.dumps(resource)


def generate_medication_data(member_id, provider_id):
    """Generate medication data"""
    meds = [
        ("64893031113", "Lisinopril", "10 mg tablet", "ORAL", "Once daily"),
        ("00173028305", "Atorvastatin", "20 mg tablet", "ORAL", "Once at bedtime"),
        ("00093313405", "Metformin", "500 mg tablet", "ORAL", "Twice daily with meals"),
        ("00172024203", "Albuterol", "90 mcg/actuation", "INHALED", "As needed for wheezing"),
        ("00310079305", "Omeprazole", "20 mg capsule", "ORAL", "Once daily before breakfast")
    ]

    med_code, med_name, dosage, route, freq = random.choice(meds)
    start_date = fake.date_between(start_date='-1y', end_date='today')
    end_date = fake.date_between(start_date=start_date, end_date='+1y') if random.random() > 0.3 else None

    return {
        "medication_id": generate_random_id("MED"),
        "member_id": member_id,
        "provider_id": provider_id,
        "medication_code": med_code,
        "medication_name": med_name,
        "dosage": dosage,
        "route": route,
        "frequency": freq,
        "start_date": start_date,
        "end_date": end_date,
        "status": random.choice(["ACTIVE", "COMPLETED", "STOPPED"]),
        "refills_remaining": random.randint(0, 5),
        "is_generic": random.choice([True, False]),
        "prescribed_at": fake.date_time_between(start_date=start_date, end_date='now'),
        "filled_at": fake.date_time_between(start_date=start_date, end_date='now') if random.random() > 0.2 else None,
        "pharmacy_info": json.dumps({
            "name": fake.company(),
            "address": generate_address(),
            "phone": fake.phone_number()
        })
    }


def generate_invoice_data(provider_id):
    """Generate invoice data"""
    start_date = fake.date_between(start_date='-6m', end_date='-1m')
    end_date = fake.date_between(start_date=start_date, end_date='today')
    total = round(random.uniform(1000, 10000), 2)
    paid = round(total * random.uniform(0.7, 1.0), 2)

    return {
        "invoice_id": generate_random_id("INV"),
        "provider_id": provider_id,
        "billing_period_start": start_date,
        "billing_period_end": end_date,
        "total_amount": total,
        "paid_amount": paid,
        "balance_due": total - paid,
        "status": random.choice(["DRAFT", "SUBMITTED", "PAID"]),
        "due_date": fake.date_between(start_date=end_date, end_date='+1m'),
        "submitted_at": fake.date_time_between(start_date=end_date, end_date='now') if random.random() > 0.3 else None,
        "paid_at": fake.date_time_between(start_date=end_date, end_date='now') if random.random() > 0.5 else None,
        "payment_terms": random.choice(["NET 30", "NET 15", "Due on receipt"]),
        "notes": fake.sentence()
    }


def generate_network_participation(provider_id):
    """Generate network participation data"""
    networks = ["NET-AETNA", "NET-BLUE", "NET-CIGNA", "NET-UNITED"]
    start_date = fake.date_between(start_date='-2y', end_date='today')
    end_date = fake.date_between(start_date=start_date, end_date='+2y') if random.random() > 0.7 else None

    return {
        "participation_id": generate_random_id("PART"),
        "provider_id": provider_id,
        "network_id": random.choice(networks),
        "participation_type": random.choice(["PRIMARY", "SECONDARY"]),
        "effective_date": start_date,
        "end_date": end_date,
        "credentialing_info": json.dumps({
            "credentialed": True,
            "credentialing_date": start_date.isoformat(),
            "next_review": fake.date_between(start_date='+1y', end_date='+2y').isoformat()
        }),
        "panel_status": random.choice(["OPEN", "CLOSED"]),
        "acceptance_terms": fake.text()
    }


def generate_payment_policy(plan_id):
    """Generate payment policy data"""
    policy_types = ["FEE_SCHEDULE", "RVU", "CAPITATION"]
    start_date = fake.date_between(start_date='-1y', end_date='today')
    end_date = fake.date_between(start_date=start_date, end_date='+2y') if random.random() > 0.5 else None

    return {
        "policy_id": generate_random_id("POL"),
        "plan_id": plan_id,
        "policy_type": random.choice(policy_types),
        "name": f"Payment Policy for {plan_id}",
        "description": fake.text(),
        "rules": json.dumps({
            "base_rate": round(random.uniform(0.8, 1.2), 2),
            "adjustments": {
                "after_hours": 1.15,
                "weekend": 1.1
            }
        }),
        "effective_date": start_date,
        "end_date": end_date,
        "is_active": random.choice([True, False]),
        "created_by": "system"
    }


def generate_plan_benefit(plan_id):
    """Generate plan benefit data"""
    benefits = [
        ("PREV", "Preventive Care", "Full coverage for preventive services", "FULL", 0, 0),
        ("HOSP", "Hospitalization", "Inpatient hospital services", "PARTIAL", 500, 20),
        ("RX", "Prescription Drugs", "Coverage for prescription medications", "PARTIAL", 20, 30),
        ("ER", "Emergency Room", "Emergency services", "PARTIAL", 250, 30),
        ("SPEC", "Specialist Visit", "Specialist physician services", "PARTIAL", 50, 30)
    ]

    code, name, desc, level, copay, coinsurance = random.choice(benefits)

    return {
        "benefit_id": generate_random_id("BEN"),
        "plan_id": plan_id,
        "benefit_code": code,
        "benefit_name": name,
        "description": desc,
        "coverage_level": level,
        "copay_amount": copay,
        "coinsurance_rate": coinsurance,
        "annual_limit": round(random.uniform(1000, 10000), 2) if random.random() > 0.5 else None,
        "is_subject_to_deductible": random.choice([True, False]),
        "effective_date": fake.date_between(start_date='-1y', end_date='today'),
        "termination_date": fake.date_between(start_date='today', end_date='+2y') if random.random() > 0.7 else None
    }


def generate_provider_contract(provider_id, plan_id):
    """Generate provider contract data"""
    start_date = fake.date_between(start_date='-1y', end_date='today')
    end_date = fake.date_between(start_date=start_date, end_date='+2y') if random.random() > 0.5 else None

    return {
        "contract_id": generate_random_id("CONT"),
        "provider_id": provider_id,
        "plan_id": plan_id,
        "contract_type": random.choice(["STANDARD", "PREFERRED"]),
        "effective_date": start_date,
        "termination_date": end_date,
        "payment_terms": json.dumps({
            "fee_schedule": "CMS",
            "payment_days": 30,
            "withhold_percentage": 10
        }),
        "termination_clause": "30 days notice required",
        "reimbursement_rate": round(random.uniform(80, 120), 2),
        "quality_bonus_rate": round(random.uniform(0, 10), 2),
        "is_active": random.choice([True, False])
    }


def generate_risk_profile(member_id):
    """Generate patient risk profile data"""
    conditions = ["Hypertension", "Diabetes", "Hyperlipidemia", "Asthma", "Depression"]
    chronic = random.sample(conditions, k=random.randint(1, 3))

    return {
        "member_id": member_id,
        "risk_score": round(random.uniform(10, 90), 2),
        "risk_category": random.choice(["LOW", "MODERATE", "HIGH"]),
        "chronic_conditions": json.dumps(chronic),
        "medications": json.dumps([f"Medication-{i}" for i in range(1, random.randint(1, 5))]),
        "yearly_claim_total": round(random.uniform(1000, 20000), 2),
        "claim_frequency": random.randint(1, 20),
        "predictive_costs": json.dumps({
            "inpatient": round(random.uniform(0, 10000), 2),
            "outpatient": round(random.uniform(0, 5000), 2),
            "pharmacy": round(random.uniform(0, 3000), 2)
        }),
        "care_gaps": json.dumps({
            "preventive": random.choice([True, False]),
            "medication_adherence": random.choice([True, False]),
            "chronic_management": random.choice([True, False])
        })
    }


def generate_report_definition():
    """Generate report definition data"""
    categories = ["CLAIMS", "MEMBERS", "PROVIDERS", "FINANCIAL", "RISK"]
    category = random.choice(categories)

    if category == "CLAIMS":
        name = "Claims Analysis Report"
        code = "CLAIMS_ANALYSIS"
        columns = ["claim_id", "member_id", "provider_id", "status", "total_billed", "total_paid"]
    elif category == "MEMBERS":
        name = "Member Demographics Report"
        code = "MEMBER_DEMO"
        columns = ["member_id", "last_name", "first_name", "dob", "gender", "coverage_status"]
    else:
        name = f"{category.capitalize()} Summary Report"
        code = f"{category}_SUMMARY"
        columns = ["id", "name", "status", "created_at"]

    return {
        "id": generate_random_id("REP"),
        "report_name": name,
        "report_code": code,
        "description": fake.text(),
        "report_category": category,
        "query_definition": json.dumps({
            "table": category.lower(),
            "filters": [],
            "sort": {"field": "created_at", "order": "DESC"}
        }),
        "output_columns": json.dumps(columns),
        "default_parameters": json.dumps({"date_range": "last_30_days"}),
        "refresh_frequency": random.choice(["DAILY", "WEEKLY", "MONTHLY"]),
        "is_system": random.choice([True, False]),
        "created_by": fake.user_name()
    }


def get_existing_data(conn):
    """Fetch existing data from database to maintain relationships"""
    with conn.cursor(dictionary=True) as cursor:
        # Get existing members
        cursor.execute("SELECT id FROM members")
        members = [row['id'] for row in cursor.fetchall()]

        # Get existing providers
        cursor.execute("SELECT id FROM providers")
        providers = [row['id'] for row in cursor.fetchall()]

        # Get existing plans
        cursor.execute("SELECT plan_id FROM health_plans")
        plans = [row['plan_id'] for row in cursor.fetchall()]

        # Get existing claims
        cursor.execute("SELECT claim_id FROM medical_claims")
        claims = [row['claim_id'] for row in cursor.fetchall()]

    return {
        "members": members,
        "providers": providers,
        "plans": plans,
        "claims": claims
    }


def insert_data(conn, table, data):
    """Insert data into specified table"""
    with conn.cursor(dictionary=True) as cursor:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
    conn.commit()


def generate_and_insert_data(conn, count=5):
    """Generate and insert data for empty tables"""
    existing = get_existing_data(conn)

    print(f"Generating data for {count} records per table...")

    # Generate data for FHIR Resources
    for _ in range(count):
        member_id = random.choice(existing["members"])
        resource_type = random.choice(["Patient", "Observation", "Condition", "Medication"])
        data = {
            "resource_id": generate_random_id("RES"),
            "member_id": member_id,
            "resource_type": resource_type,
            "raw_resource": generate_fhir_resource(member_id, resource_type),
            "clinical_summary": fake.text(),
            "last_updated": fake.date_time_this_year(),
            "is_active": random.choice([True, False]),
            "source_system": random.choice(["EPIC", "CERNER", "ATENA", "INTERNAL"])
        }
        insert_data(conn, "fhir_resources", data)

    # Generate data for Medications
    for _ in range(count):
        member_id = random.choice(existing["members"])
        provider_id = random.choice(existing["providers"])
        data = generate_medication_data(member_id, provider_id)
        insert_data(conn, "medications", data)

    # Generate data for Invoices
    for _ in range(count):
        provider_id = random.choice(existing["providers"])
        data = generate_invoice_data(provider_id)
        insert_data(conn, "invoices", data)

    # Generate data for Network Participations
    for _ in range(count):
        provider_id = random.choice(existing["providers"])
        data = generate_network_participation(provider_id)
        insert_data(conn, "network_participations", data)

    # Generate data for Payment Policies
    for _ in range(count):
        plan_id = random.choice(existing["plans"])
        data = generate_payment_policy(plan_id)
        insert_data(conn, "payment_policies", data)

    # Generate data for Plan Benefits
    for _ in range(count):
        plan_id = random.choice(existing["plans"])
        data = generate_plan_benefit(plan_id)
        insert_data(conn, "plan_benefits", data)

    # Generate data for Provider Contracts
    for _ in range(count):
        provider_id = random.choice(existing["providers"])
        plan_id = random.choice(existing["plans"])
        data = generate_provider_contract(provider_id, plan_id)
        insert_data(conn, "provider_contracts", data)

    # Generate data for Patient Risk Profiles
    for member_id in existing["members"]:  # One per member
        data = generate_risk_profile(member_id)
        insert_data(conn, "patient_risk_profiles", data)

    # Generate data for Report Definitions
    for _ in range(count):
        data = generate_report_definition()
        insert_data(conn, "report_definitions", data)

    print("Data generation and insertion completed successfully!")


def main():
    try:
        # Connect to the database
        connection = mysql.connector.connect(**DB_CONFIG)

        # Generate and insert data
        generate_and_insert_data(connection, count=5)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection and connection.is_connected:
            connection.close()


if __name__ == "__main__":
    main()