import os

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'unsc-kdn-json-bucket')
APP_AWS_REGION = os.environ.get('APP_AWS_REGION', 'ap-southeast-1')
UN_SECURITY_COUNCIL_URL = "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list"
UNSC_S3_OBJECT_KEY = 'unsc/UNSCR_SANCTION_LIST.json'
KDN_MOHA_URL = "https://www.moha.gov.my/index.php/en/maklumat-perkhidmatan/membanteras-pembiayaan-keganasan2/senarai-kementerian-dalam-negeri"
KDN_LAST_XML_URL_KEY = 'kdn/kdn_last_xml_url.txt'
KDN_INDIVIDUALS_S3_KEY = 'kdn/KDN_INDIVIDUAL_SANCTION_LIST.json'
KDN_GROUPS_S3_KEY = 'kdn/KDN_GROUP_SANCTION_LIST.json'
UNSC_LAST_XML_HASH_KEY = 'unsc/unsc_last_xml_content_hash.txt'
LOCAL_OUTPUT_DIRECTORY = 'local_output' 