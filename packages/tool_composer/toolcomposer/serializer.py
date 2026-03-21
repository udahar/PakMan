"""
Pipeline Serializer - JSON import/export for pipelines.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from toolcomposer.models import PipelineConfig


class PipelineSerializer:
    """
    Handles serialization and deserialization of pipelines.

    Features:
    - JSON export/import
    - File I/O
    - Validation
    """

    def __init__(self):
        self.logger = logging.getLogger("PipelineSerializer")

    def to_json(self, pipeline: PipelineConfig, indent: int = 2) -> str:
        """
        Serialize a pipeline to JSON string.

        Args:
            pipeline: PipelineConfig to serialize
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        try:
            return json.dumps(pipeline.to_dict(), indent=indent)
        except Exception as e:
            self.logger.error(f"Serialization failed: {e}")
            raise

    def from_json(self, json_str: str) -> PipelineConfig:
        """
        Deserialize a pipeline from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            PipelineConfig instance
        """
        try:
            data = json.loads(json_str)
            return PipelineConfig.from_dict(data)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Deserialization failed: {e}")
            raise

    def save_to_file(self, pipeline: PipelineConfig, path: str) -> bool:
        """
        Save a pipeline to a file.

        Args:
            pipeline: PipelineConfig to save
            path: File path to save to

        Returns:
            True if successful
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            json_str = self.to_json(pipeline)
            file_path.write_text(json_str)

            self.logger.info(f"Pipeline saved to: {path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save pipeline: {e}")
            return False

    def load_from_file(self, path: str) -> Optional[PipelineConfig]:
        """
        Load a pipeline from a file.

        Args:
            path: File path to load from

        Returns:
            PipelineConfig instance or None if failed
        """
        try:
            file_path = Path(path)

            if not file_path.exists():
                self.logger.error(f"File not found: {path}")
                return None

            json_str = file_path.read_text()
            return self.from_json(json_str)

        except Exception as e:
            self.logger.error(f"Failed to load pipeline: {e}")
            return None

    def validate(self, pipeline: PipelineConfig) -> tuple[bool, list[str]]:
        """
        Validate a pipeline configuration.

        Args:
            pipeline: PipelineConfig to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check for required fields
        if not pipeline.id:
            errors.append("Pipeline ID is required")

        if not pipeline.name:
            errors.append("Pipeline name is required")

        # Check for nodes
        if not pipeline.nodes:
            errors.append("Pipeline must have at least one node")

        # Check for duplicate node IDs
        node_ids = [n.id for n in pipeline.nodes]
        duplicates = set([x for x in node_ids if node_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Duplicate node IDs: {duplicates}")

        # Check edge references
        node_id_set = set(node_ids)
        for edge in pipeline.edges:
            if edge.source_node not in node_id_set:
                errors.append(f"Edge references unknown source node: {edge.source_node}")
            if edge.target_node not in node_id_set:
                errors.append(f"Edge references unknown target node: {edge.target_node}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_summary(self, pipeline: PipelineConfig) -> dict:
        """
        Get a summary of the pipeline.

        Args:
            pipeline: PipelineConfig to summarize

        Returns:
            Dictionary with pipeline summary
        """
        node_types = {}
        for node in pipeline.nodes:
            node_types[node.type] = node_types.get(node.type, 0) + 1

        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "description": pipeline.description,
            "node_count": len(pipeline.nodes),
            "edge_count": len(pipeline.edges),
            "node_types": node_types,
            "version": pipeline.version,
        }


# Convenience functions
def save_pipeline(pipeline: PipelineConfig, path: str) -> bool:
    """Save a pipeline to a file."""
    serializer = PipelineSerializer()
    return serializer.save_to_file(pipeline, path)


def load_pipeline(path: str) -> Optional[PipelineConfig]:
    """Load a pipeline from a file."""
    serializer = PipelineSerializer()
    return serializer.load_from_file(path)


def validate_pipeline(pipeline: PipelineConfig) -> tuple[bool, list[str]]:
    """Validate a pipeline configuration."""
    serializer = PipelineSerializer()
    return serializer.validate(pipeline)
