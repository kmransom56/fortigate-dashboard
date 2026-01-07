import sys
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# Add DATASTORE logic to sys.path
sys.path.append("/media/keith/DATASTORE/network-device-mcp-server/src")

try:
    from ltm_core.voice_learning import VoiceLearningEngine, CommandIntent
    from ltm_core.ltm_memory import LTMMemorySystem
    LOGIC_AVAILABLE = True
except ImportError:
    LOGIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceIntelligenceBridge:
    """
    Bridges the 'Crown Jewel' voice logic from the DATASTORE NOC platform
    into the Enterprise Showcase.
    """
    
    def __init__(self):
        self.available = LOGIC_AVAILABLE
        if LOGIC_AVAILABLE:
            # Note: In a real run, LTMMemorySystem might need DB config
            # Here we initialize with defaults to capture the logic intent
            try:
                self.memory = LTMMemorySystem() 
                self.engine = VoiceLearningEngine(ltm_memory=self.memory)
            except Exception as e:
                logger.error(f"Failed to initialize voice engine: {e}")
                self.available = False

    def process_command(self, text: str) -> Dict[str, Any]:
        """
        Processes a voice command text and routes it to integrated services.
        Example: 'Investigate Sonic store 155'
        """
        if not self.available:
            return {
                "status": "simulated",
                "text": text,
                "intent": "Unknown",
                "response": "Voice Learning Logic currently offline in DATASTORE."
            }
        
        # Leverage the real learning engine from /ltm_core/
        command = self.engine.process_voice_command(text)
        
        return {
            "status": "active",
            "command_id": command.command_id,
            "intent": command.intent.value,
            "entities": command.entities,
            "confidence": f"{command.confidence * 100:.1f}%",
            "response": self._generate_noc_response(command)
        }

    def _generate_noc_response(self, command: Any) -> str:
        """Heuristic response generator based on NOC platform patterns."""
        intent = command.intent.value
        entities = command.entities
        
        if intent == "investigation":
            brand = entities.get('brand', 'Unknown')
            store = entities.get('store_id', 'Unknown')
            return f"Initiating high-fidelity scan for {brand} Store {store}. Checking LTM behavior patterns..."
        
        if intent == "navigation":
            dest = entities.get('destination', 'Dashboard')
            return f"Switching context to {dest}..."
            
        return f"Voice command recognized as {intent}. Executing integrated logic..."

voice_service = VoiceIntelligenceBridge()
