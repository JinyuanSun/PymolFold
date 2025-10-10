from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Dict, Any, Optional, List
from pathlib import Path


class StructurePredictor(ABC):
    """Base class for all structure prediction methods"""

    def __init__(self, workdir: Optional[str] = None):
        """Initialize predictor with optional working directory

        Args:
            workdir: Directory to save prediction results. Defaults to current directory.
        """
        self.workdir = Path(workdir) if workdir else Path.cwd()
        self.workdir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def predict(self, sequence: str, **kwargs) -> Dict[str, Any]:
        """Predict structure from sequence

        Args:
            sequence: Amino acid sequence
            **kwargs: Additional method-specific parameters

        Returns:
            Dictionary containing prediction results including:
            - structures: List of structure dictionaries with 'structure' and 'source' fields
            - confidence_scores: List of confidence scores
            - additional method-specific results
        """
        pass

    def save_structures(self, result: Dict[str, Any], name=None) -> List[Path]:
        """Save predicted structures to files

        Args:
            result: Dictionary returned by predict()

        Returns:
            List of paths to saved structure files
        """
        saved_files = []
        for i, struct in enumerate(result.get("structures", [])):
            initial_name = deepcopy(name)
            if "structure" not in struct or "source" not in struct:
                continue
            if initial_name is None:
                # Clean filename and ensure .cif extension
                initial_name = self._clean_filename(struct["source"])
            else:
                initial_name += f"_{i + 1}"
            suffix = ".cif" if struct["structure"].startswith("data_") else ".pdb"
            if not initial_name.lower().endswith(suffix):
                initial_name += suffix

            # Avoid name collisions
            path = self.workdir / initial_name
            counter = 1
            while path.exists():
                stem = Path(initial_name).stem
                if stem.endswith(f"_{counter - 1}"):
                    stem = stem.rsplit("_", 1)[0]
                path = self.workdir / f"{stem}_{counter}{suffix}"
                counter += 1

            # Save structure
            path.write_text(struct["structure"])
            saved_files.append(path)
        return saved_files

    @staticmethod
    def _clean_filename(name: str) -> str:
        """Clean a string to create a valid filename"""
        # Remove/replace invalid characters
        name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
        # Remove leading/trailing spaces and dots
        name = name.strip(". ")
        # Collapse multiple spaces/underscores
        name = "_".join(filter(None, name.split()))
        return name or "structure"
