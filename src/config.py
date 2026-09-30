import os
from google import genai

PROJECT_ID = "822652243793"

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location="northamerica-northeast1"
)

LLM_MODEL = "gemini-3.5-flash"
EMBEDDING_MODEL = "text-embedding-005"

QUEBEC_SOURCES = [
    # Regulations
    "https://lautorite.qc.ca/en/general-public/insurance/group-insurance",
    "https://web.archive.org/web/2/https://www.ramq.gouv.qc.ca/en/citizens/prescription-drug-insurance",
    "https://www.ramq.gouv.qc.ca/en/citizens/health-insurance/know-eligibility-conditions",
    "https://legisquebec.gouv.qc.ca/en/showdoc/cs/A-29.01",
    "https://educaloi.qc.ca/",

    # Insurers
    "https://web.archive.org/web/https://www.sunlife.ca/en/group/benefits/",
    "https://web.archive.org/web/2/https://www.manulife.ca/business/group-benefits.html",
    "https://www.canadalife.com/insurance/workplace-benefits.html",
    "https://www.empire.ca/group-benefits",
    "https://ia.ca/business/insights/group-insurance",
    "https://www.uvassurance.ca/en/group-insurance/",
    "https://www.humania.ca/en/en/advisor-centre/group-insurance-advisor/",
    "https://www.greenshield.ca/en-ca/insurance/comprehensive-benefits",
    "https://www.desjardins.com/en/insurance/group.html",
    "https://www.beneva.ca/en/group-insurance",

    # Third-parties (TPAs, MGAs, etc.)
    "https://www.bbd.ca/",
    "https://www.aga.ca/",
    "https://gpm.ca/",
    "https://rvavantagessociaux.ca/",
    "https://web.archive.org/web/https://assuredirect.ca/blogue/"
]
