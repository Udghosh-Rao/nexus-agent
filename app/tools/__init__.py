from app.tools.finance import analyze_finance, detect_risk
from app.tools.general import GENERAL_TOOLS

FINANCE_TOOLS = [analyze_finance, detect_risk]
ALL_PRIMARY_TOOLS = FINANCE_TOOLS + GENERAL_TOOLS
