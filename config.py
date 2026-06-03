# config.py - All settings for the project

# LM Studio settings
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_API_KEY  = "lm-studio"
HERMES_MODEL       = "nous-hermes-2-mistral-7b-dpo"

# Agent settings
MAX_ITERATIONS       = 3      # how many times agents retry
COMPLIANCE_THRESHOLD = 0.80   # 80% score needed to pass

# Folder paths
OUTPUTS_DIR     = "outputs"
SAMPLE_DOCS_DIR = "sample_docs"
MEMORY_FILE     = "memory/memory.json"
AUDIT_LOG_FILE  = "outputs/audit_log.json"

# Output settings
CONFIDENCE_PASS_MARK = 0.80