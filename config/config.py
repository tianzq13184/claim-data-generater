"""
Configuration settings for the claim data generator
"""

# EDI Configuration
COMPANY_ID = "COMPANYXX"
SENDER_ID = "SENDERID"
RECEIVER_ID = "RECEIVERID"
ANONYMIZE_DATA = True
BATCH_SIZE = 100  # Process in batches to manage memory

# Database Configuration
# Production database (commented out)
# DB_CONFIG = {
#     'host': 'insurance.cpy2e6qoaeck.ap-southeast-2.rds.amazonaws.com',
#     'database': 'insurance',
#     'user': 'root',
#     'password': 'Insurance_2025'
# }

# Development database
DB_CONFIG = {
    'host': '192.168.10.20',
    'database': 'insurance',
    'user': 'root',
    'password': '123456'
}

# File paths
DATA_DIR = "data"
SAMPLES_DIR = "data/samples"
OUTPUT_DIR = "data/output"

