"""
Sabit değerler: dizin yolları ve health score ağırlıkları.
"""
import os

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "outputs")

# Health Score ağırlıkları (main.py'den taşındı)
HEALTH_MISSING_WEIGHT = 1.00
HEALTH_FORMAT_WEIGHT = 0.50
HEALTH_OUTLIER_WEIGHT = 0.25
