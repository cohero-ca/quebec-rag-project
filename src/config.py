# src/config.py

CORE_QUEBEC_SOURCES = [
    # Regulations
    "https://lautorite.qc.ca/en/general-public/insurance/group-insurance",
    "https://web.archive.org/web/2/https://www.ramq.gouv.qc.ca/en/citizens/prescription-drug-insurance",
    "https://web.archive.org/web/https://www.ramq.gouv.qc.ca/en/citizens/health-insurance/know-eligibility-conditions",
    "https://legisquebec.gouv.qc.ca/en/showdoc/cs/A-29.01",
    "https://educaloi.qc.ca/",
    "https://www.cnesst.gouv.qc.ca/fr/conditions-travail/categories-travailleuses-travailleurs/travailleuses-travailleurs-non-vises",
    "https://www.cnesst.gouv.qc.ca/fr/demarches-formulaires/employeurs/assurance-sante-securite-travail/types-protection/protection-personnelle",
    "https://www.rcgt.com/fr/planiguide/modules/module-12-programmes-et-charges-sociales/assurance-emploi-et-regime-quebecois-dassurance-parentale/",
    "https://www.rcgt.com/fr/planiguide/modules/module-05-employes/avantages-non-imposables/",
    "https://www.sunlife.ca/fr/collective/epargne-retraite/vos-avantages-sociaux-imposables-ou-non/",
    # Primary Insurers
    "https://web.archive.org/web/https://www.sunlife.ca/en/group/benefits/",
    "https://web.archive.org/web/2/https://www.manulife.ca/business/group-benefits.html",
    "https://www.canadalife.com/insurance/workplace-benefits.html",
    "https://www.empire.ca/group-benefits",
    "https://ia.ca/business/insights/group-insurance",
    "https://www.uvassurance.ca/en/group-insurance/",
    "https://www.humania.ca/en/en/advisor-centre/group-insurance-advisor/",
    "https://www.greenshield.ca/en-ca/insurance/comprehensive-benefits",
    "https://www.desjardins.com/en/insurance/group.html",
    "https://web.archive.org/web/https://www.beneva.ca/en/group-insurance",
]

THIRD_PARTY_SOURCES = [
    # TPAs, MGAs, and Blogs
    "https://www.bbd.ca/",
    "https://www.aga.ca/",
    "https://gpm.ca/",
    "https://web.archive.org/web/https://rvavantagessociaux.ca/",
    "https://web.archive.org/web/https://assuredirect.ca/blogue/",
]

# Combined lookup map with category tags
SOURCE_CATEGORIES = {
    url: "core" for url in CORE_QUEBEC_SOURCES
} | {
    url: "third_party" for url in THIRD_PARTY_SOURCES
}

QUEBEC_SOURCES = CORE_QUEBEC_SOURCES + THIRD_PARTY_SOURCES