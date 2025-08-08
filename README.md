# UNSC & KDN Sanction List Web Scraper

Automated AWS Lambda application that scrapes, processes, and monitors changes in:
- **UNSC**: UN Security Council Consolidated Sanction List (XML → JSON)
- **KDN**: Malaysian Ministry of Home Affairs Sanction List (PDF → JSON)

## Quick Start

### Local Testing
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run locally (outputs to local_output/ directory)
python main.py
```

### AWS Deployment
```bash
# 1. Build and push Docker image
docker build -t sanction-list-processor .
aws ecr create-repository --repository-name sanction-list-processor --region <YOUR_REGION>
aws ecr get-login-password --region <YOUR_REGION> | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
docker tag sanction-list-processor:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/sanction-list-processor:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/sanction-list-processor:latest

# 2. Create Lambda function using container image from ECR
# 3. Set environment variables: S3_BUCKET_NAME, APP_AWS_REGION
# 4. Configure IAM role with S3 and CloudWatch permissions
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   UNSC Website  │───▶│  Lambda Function │───▶│   S3 Bucket     │
│   (XML Files)   │    │                  │    │  (JSON Output)  │
└─────────────────┘    │                  │    └─────────────────┘
                       │                  │
┌─────────────────┐    │                  │    ┌─────────────────┐
│   KDN Website   │───▶│  Change Detection│───▶│  State Tracking │
│   (PDF Files)   │    │  & Processing    │    │ (Hash/URL Files)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Change Detection:**
- **UNSC**: SHA256 hash of XML content
- **KDN**: XML URL comparison

**Key Features:**
- Only processes when changes detected
- Handles both local testing and AWS production
- Robust error handling and logging
- SSL verification disabled for KDN (legacy system requirement)

## Project Structure

```
├── main.py                    # Main Lambda handler & orchestration
├── config/settings.py         # Configuration & environment variables
├── UNSC/
│   ├── unsc_web_scraper.py   # UNSC website scraping
│   └── unsc_xml_parser.py    # XML to JSON conversion
├── KDN/
│   ├── kdn_web_scraper.py    # KDN website scraping & PDF download
│   └── kdn_pdf_parser.py     # PDF parsing & JSON conversion
├── utils/
│   ├── aws_s3_utils.py       # S3 operations
│   ├── common_utils.py       # Shared utilities (hashing, date parsing)
│   └── local_file_utils.py   # Local testing file operations
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
└── local_output/           # Local testing output directory
```

## Local Development

### Requirements
- Python 3.9+
- Required packages: `boto3`, `requests`, `beautifulsoup4`, `xmltodict`, `pdfplumber`

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Local Mode Behavior
- Saves JSON files to `local_output/` directory
- Stores state files locally (hash/URL tracking)
- Uses `local_file_utils.py` for file operations
- No AWS credentials required for local testing

### Output Files
```
local_output/
├── UNSCR_SANCTION_LIST.json           # UNSC processed data
├── KDN_INDIVIDUAL_SANCTION_LIST.json  # KDN individuals
├── KDN_GROUP_SANCTION_LIST.json       # KDN groups
├── unsc_last_xml_content_hash.txt     # UNSC change tracking
└── kdn_last_xml_url.txt               # KDN change tracking
```

## AWS Deployment

### Prerequisites
- Docker installed and running
- AWS CLI configured with appropriate permissions
- IAM user with ECR and Lambda permissions

### Step 1: Container Image Setup
```bash
# Build Docker image
docker build -t sanction-list-processor .

# Create ECR repository
aws ecr create-repository --repository-name sanction-list-processor --region <YOUR_REGION>

# Get login token and authenticate
aws ecr get-login-password --region <YOUR_REGION> | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

# Tag and push image
docker tag sanction-list-processor:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/sanction-list-processor:latest
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/sanction-list-processor:latest
```

### Step 2: Lambda Function Configuration

**Basic Settings:**
- **Runtime**: Container Image
- **Architecture**: x86_64
- **Memory**: 512-1024 MB (PDF processing is memory-intensive)
- **Timeout**: 3-5 minutes (network latency + processing time)

**Environment Variables:**
```
S3_BUCKET_NAME=your-bucket-name
APP_AWS_REGION=ap-southeast-1
```

**IAM Execution Role Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream", 
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

### Step 3: S3 Bucket Setup
- Create bucket in same region as Lambda
- Enable versioning (recommended)
- Configure lifecycle policies if needed

### Step 4: Automated Scheduling (Optional)
Add EventBridge trigger with cron expression:
- Daily: `cron(0 0 * * ? *)`
- Hourly: `cron(0 * * * ? *)`

## Configuration Reference

### Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `S3_BUCKET_NAME` | S3 bucket for JSON output | `unsc-kdn-json-bucket` |
| `APP_AWS_REGION` | AWS region | `ap-southeast-1` |

### Source URLs (configured in settings.py)
| Source | URL | Purpose |
|--------|-----|---------|
| UNSC | `https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list` | XML sanction list |
| KDN | `https://www.moha.gov.my/index.php/en/maklumat-perkhidmatan/membanteras-pembiayaan-keganasan2/senarai-kementerian-dalam-negeri` | PDF sanction list |

### Output Structure
**S3 Paths:**
```
s3://your-bucket/
├── unsc/
│   ├── UNSCR_SANCTION_LIST.json
│   └── unsc_last_xml_content_hash.txt
└── kdn/
    ├── KDN_INDIVIDUAL_SANCTION_LIST.json
    ├── KDN_GROUP_SANCTION_LIST.json
    └── kdn_last_xml_url.txt
```

## Key Functions

### main.py
- `lambda_handler()`: AWS Lambda entry point
- `run_unsc_sanction_list_process()`: UNSC processing pipeline
- `run_kdn_sanction_list_process()`: KDN processing pipeline

### Change Detection Logic
**UNSC:** Downloads XML → calculates SHA256 hash → compares with stored hash → processes if different
**KDN:** Scrapes current XML URL → compares with stored URL → downloads PDF if changed

### Error Handling
- Comprehensive logging to CloudWatch
- Graceful degradation on individual source failures
- Network timeout and retry logic
- State consistency protection

## Security Considerations

### SSL Verification
- **UNSC**: `verify=True` (standard SSL verification)
- **KDN**: `verify=False` (Does not work with SSL verification)

### IAM Best Practices
- Use least-privilege IAM policies
- Separate roles for deployment vs runtime
- Regular credential rotation
- Monitor access patterns via CloudTrail

## Troubleshooting

### Common Issues

**Lambda timeout:**
- Increase timeout setting (current: 3-5 minutes recommended)
- Check network latency in CloudWatch logs

**Memory errors:**
- Increase memory allocation (PDF processing is memory-intensive)
- Current recommendation: 512-1024 MB

**Permission denied:**
- Verify IAM role has S3 permissions
- Check bucket policy and region consistency

**SSL certificate errors (KDN):**
- Expected behavior due to `verify=False` setting
- Monitor logs for network connectivity issues

**Change detection not working:**
- Check state file integrity in S3/local_output
- Verify hash calculation consistency

### Debugging Steps
1. Check CloudWatch Logs: Lambda → Monitor → View logs in CloudWatch
2. Verify environment variables: Configuration → Environment variables
3. Test locally: `python main.py` to isolate AWS vs code issues
4. Check S3 permissions: Try manual S3 operations with same role
5. Validate Docker image: Test container locally before deployment

### Log Analysis
**Normal execution logs:**
```
Starting UN Sanction List update check
Found UN XML link: https://...
Current UN XML content hash: abc123...
UNSC XML content has changed! Proceeding to parse and upload.
Successfully uploaded to s3://bucket/unsc/UNSCR_SANCTION_LIST.json
```

**Change detection (no processing):**
```
UNSC XML content has not changed since last check. Skipping processing.
KDN XML link not updated. Skipping PDF content download and processing.
```

---

## TL;DR

**What it does**: Scrapes UNSC (XML) and KDN (PDF) sanction lists, converts to JSON, stores in S3. Only processes when changes detected.

**Local testing**: `python main.py` → outputs to `local_output/`

**AWS deployment**: Build Docker → Push to ECR → Create Lambda with container image → Set env vars (`S3_BUCKET_NAME`, `APP_AWS_REGION`) → Configure IAM role with S3 permissions

**Key files**: 
- `main.py` (orchestrator)
- `config/settings.py` (configuration)
- `UNSC/` (UN processing)
- `KDN/` (Malaysian processing)
- `utils/` (AWS & common utilities)

**Change detection**: UNSC uses content hash, KDN uses URL comparison

**Critical settings**: 512-1024MB memory, 3-5min timeout, proper IAM permissions

**Troubleshooting**: Check CloudWatch logs, verify IAM permissions, test locally first

**Security note**: KDN uses `verify=False` for SSL