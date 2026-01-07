import sys
import logging
from typing import Dict, Any

# Add the meraki-magic-mcp reusable package to PYTHONPATH
sys.path.append('/media/keith/DATASTORE/meraki-magic-mcp/reusable')

try:
    from ai_assistant import AIAssistant
except ImportError as e:
    raise ImportError(f"Failed to import AIAssistant from meraki-magic-mcp: {e}")

logger = logging.getLogger(__name__)

class AIIntelligenceService:
    """Facade over the Meraki‑Magic‑MCP AIAssistant.

    Provides high‑level operations that the dashboard can call:
    - audit
    - repair
    - update
    - optimize
    - learn
    - predict (uses the existing LTM predictive service)
    """

    def __init__(self):
        # Initialise the assistant with a generic app name; it will manage its own key storage.
        self.assistant = AIAssistant(app_name="fortigate_dashboard")
        if not self.assistant.agent.is_available():
            logger.warning("AI backend not available – endpoints will return a fallback response.")

    # ---------------------------------------------------------------------
    # Core operations – thin wrappers that forward arguments to the assistant.
    # ---------------------------------------------------------------------
    def audit(self, target: str, audit_type: str = "code") -> Dict[str, Any]:
        return self.assistant.audit(target, audit_type)

    def repair(self, issue_description: str, code_path: str | None = None) -> Dict[str, Any]:
        return self.assistant.repair(issue_description, code_path)

    def update(self, update_type: str = "dependencies", target: str | None = None) -> Dict[str, Any]:
        return self.assistant.update(update_type, target)

    def optimize(self, target: str, optimization_type: str = "performance") -> Dict[str, Any]:
        return self.assistant.optimize(target, optimization_type)

    def learn(self, source: str, topic: str | None = None) -> Dict[str, Any]:
        return self.assistant.learn(source, topic)

    # Predictive alerts are already provided by the LTM service; this method simply forwards.
    def predict(self, brand: str = "all") -> Dict[str, Any]:
        # The LTM service lives in app.services.ltm_service as ltm_service
        try:
            from app.services.ltm_service import ltm_service
            return {"predictions": ltm_service.get_predictive_alerts(brand)}
        except Exception as e:
            logger.error(f"Failed to fetch LTM predictions: {e}")
            return {"error": str(e)}

# Create a singleton instance for FastAPI injection
ai_intelligence_service = AIIntelligenceService()
