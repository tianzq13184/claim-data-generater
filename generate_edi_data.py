import random
import string
from datetime import datetime, timedelta
from faker import Faker
from mimesis import Person, Address, Datetime
from mimesis.builtins import USASpecProvider
import json
from collections import defaultdict

# Initialize data generation tools
fake = Faker('en_US')
person = Person('en')
address = Address('en')
usa = USASpecProvider()

# Global constants
COMPANY_ID = "COMPANYXX"
SENDER_ID = "SENDERID"
RECEIVER_ID = "RECEIVERID"
ANONYMIZE_DATA = True
BATCH_SIZE = 100  # Process in batches to manage memory

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
    # ISA segment
    segments.append(
        "ISA*00*          *00*          *ZZ*{sender}*ZZ*{receiver}*{date}*{time}*U*00401*{control_num}*0*P*:~".format(
            sender=SENDER_ID.ljust(15),
            receiver=RECEIVER_ID.ljust(15),
            date=current_date.strftime("%y%m%d"),
            time=current_date.strftime("%H%M"),
            control_num=generate_id("", 9)
        ))

    # GS segment
    if transaction_type == "834":
        gs_code = "BE"
        version = "004010X095A1"
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
    return segments


def generate_edi_834(num_members=1000, output_file="edi_834_large_sample.txt"):
    """Generate EDI 834 file for large number of members"""
    print(f"Generating EDI 834 data for {num_members} members...")

    segments = []
    current_date = datetime.now()

    # Generate ISA and GS segments
    segments.extend(generate_isa_gs_segments("834", current_date))

    # ST segment
    segments.append("ST*834*0001*005010X220A1~")

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
    segments.append("SE*{count}*0001~".format(count=len(segments) + 1))
    segments.append("GE*1*1~")
    segments.append("IEA*1*{control_num}~".format(control_num=generate_id("", 9)))

    # Write to file
    with open(output_file, "w",encoding='utf8') as f:
        f.write("\n".join(segments))

    print(f"Successfully generated EDI 834 data for {num_members} members in {output_file}")
    return "\n".join(segments)


def generate_edi_837(num_claims=None, claims_per_member=3, output_file="edi_837_large_sample.txt"):
    """Generate EDI 837 file with claims for all members"""
    if not global_data['members']:
        print("No members found. Generating sample members first...")
        generate_edi_834(1000)

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

    # Generate ISA and GS segments
    segments.extend(generate_isa_gs_segments("837", current_date))

    # ST segment
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

        # CLM segment - Claim info
        billed_amount = round(random.uniform(100, 5000), 2)
        claim_status = random.choice(["1", "2", "3", "4", "19", "20", "21", "22"])
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

        # Diagnosis codes
        diag_codes = random.sample([
            {"code": "J18.9", "description": "Pneumonia, unspecified"},
            {"code": "E11.65", "description": "Type 2 diabetes mellitus with hyperglycemia"},
            {"code": "I10", "description": "Essential (primary) hypertension"},
            {"code": "M54.5", "description": "Low back pain"},
            {"code": "Z79.899", "description": "Other long term drug therapy"}
        ], k=random.randint(1, 3))

        for diag in diag_codes:
            segments.append(f"HI*ABK:{diag['code']}~")

        # Service line items
        line_amounts = []
        remaining_amount = billed_amount
        for line_num in range(1, random.randint(2, 5)):
            if line_num == random.randint(2, 5) or line_num == 1:
                line_amount = round(remaining_amount, 2)
            else:
                line_amount = round(remaining_amount * random.uniform(0.2, 0.4), 2)
            remaining_amount -= line_amount
            line_amounts.append(line_amount)

            procedure_code = random.choice(["99213", "99214", "99203", "99204", "99215", "99244"])
            modifier = random.choice(["", "25", "59", "76"])
            place_of_service = random.choice(["11", "12", "21", "22"])

            segments.append(f"LX*{line_num}~")
            segments.append(f"SV1*HC:{procedure_code}{':' + modifier if modifier else ''}*{line_amount}*UN*1***1~")
            segments.append(f"REF*6R*{place_of_service}~")
            segments.append(f"DTP*472*D8*{service_date.strftime('%Y%m%d')}~")

    # End segments
    segments.append("SE*{count}*0001~".format(count=len(segments) + 1))
    segments.append("GE*1*1~")
    segments.append("IEA*1*{control_num}~".format(control_num=generate_id("", 9)))

    # Write to file
    with open(output_file, "w",encoding='utf8') as f:
        f.write("\n".join(segments))

    print(f"Successfully generated EDI 837 data with {num_claims} claims in {output_file}")
    return "\n".join(segments)

def generate_edi_835(num_payments=500, output_file="edi_835_large_sample.txt"):
    """Generate EDI 835 payment file for a subset of claims"""
    segments = []
    current_date = datetime.now()

    # If no claims exist, generate some first
    if not global_data['claims']:
        print("No claims found. Generating sample claims first...")
        generate_edi_837()

    claims = list(global_data['claims'].values())
    if len(claims) < num_payments:
        num_payments = len(claims)

    # Select random claims for payment
    paid_claims = random.sample(claims, num_payments)

    # Generate ISA and GS segments
    segments.extend(generate_isa_gs_segments("835", current_date))

    # ST segment
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
    segments.append("SE*{count}*0001~".format(count=len(segments) + 1))
    segments.append("GE*1*1~")
    segments.append("IEA*1*{control_num}~".format(control_num=generate_id("", 9)))

    # Write to file
    with open(output_file, "w") as f:
        f.write("\n".join(segments))

    print(f"Successfully generated EDI 835 data with {num_payments} payments in {output_file}")
    return "\n".join(segments)


def generate_edi_files():
    """Generate all EDI files with large datasets"""
    # Generate EDI 834 with 1000 members
    generate_edi_834(1000)

    # Generate EDI 837 with approximately 3 claims per member (3000 claims)
    generate_edi_837(claims_per_member=3)

    # Generate EDI 835 payments for a subset of claims
    generate_edi_835(num_payments=500)  # Pay about half of the claims

    print("Generated large EDI 834, 837 and 835 sample files.")


if __name__ == "__main__":
    generate_edi_files()