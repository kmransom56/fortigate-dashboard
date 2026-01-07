import os
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

VIS_DIR = Path('/media/keith/DATASTORE/cisco-meraki-cli/visualizations')

class MerakiVisualizationService:
    """Expose Meraki CLI visualizations for the dashboard.

    Provides a list of available visualizations (HTML/JS bundles) and
    a helper to generate URLs for the static files.
    """

    def __init__(self):
        if not VIS_DIR.exists():
            logger.warning('Meraki visualizations directory not found: %s', VIS_DIR)
        self.base_path = VIS_DIR

    def list_visualizations(self) -> List[Dict[str, str]]:
        """Return a list of visualizations with name and URL.

        The dashboard can render these in an iframe or embed them.
        """
        visualizations = []
        if not self.base_path.exists():
            return visualizations
        for entry in self.base_path.iterdir():
            if entry.is_file() and entry.suffix in {'.html', '.js'}:
                visualizations.append({
                    'name': entry.name,
                    'url': f'/meraki-visualizations/{entry.name}'
                })
        return visualizations

meraki_visualization_service = MerakiVisualizationService()
