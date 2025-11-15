"""Model registry for tracking ML models."""

import os
import json
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

REGISTRY_FILE = "app/ml/saved_models/model_registry.json"


class ModelRegistry:
    """Registry for tracking ML model versions and metadata."""

    def __init__(self, registry_path: str = REGISTRY_FILE):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def register_model(
        self,
        model_path: str,
        metrics: Dict,
        feature_names: list,
        training_date: Optional[datetime] = None,
    ) -> None:
        """Register a new model in the registry."""
        registry = self._load_registry()

        model_entry = {
            "model_path": model_path,
            "metrics": metrics,
            "feature_names": feature_names,
            "training_date": (training_date or datetime.utcnow()).isoformat(),
            "registered_at": datetime.utcnow().isoformat(),
        }

        registry["models"].append(model_entry)
        registry["latest"] = model_entry
        registry["updated_at"] = datetime.utcnow().isoformat()

        self._save_registry(registry)
        logger.info(f"Model registered: {model_path}")

    def get_latest_model(self) -> Optional[Dict]:
        """Get the latest model entry."""
        registry = self._load_registry()
        return registry.get("latest")

    def _load_registry(self) -> Dict:
        """Load registry from file."""
        if not self.registry_path.exists():
            return {
                "models": [],
                "latest": None,
                "updated_at": None,
            }

        try:
            with open(self.registry_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            return {
                "models": [],
                "latest": None,
                "updated_at": None,
            }

    def _save_registry(self, registry: Dict) -> None:
        """Save registry to file."""
        try:
            with open(self.registry_path, "w") as f:
                json.dump(registry, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")


def get_registry() -> ModelRegistry:
    """Get model registry instance."""
    return ModelRegistry()

