"""Pydantic models for Malloy resources."""

from typing import Any

from pydantic import BaseModel, Field


class MalloyPackageMetadata(BaseModel):
    """Metadata for a Malloy package."""

    name: str = Field(..., description="Name of the package")
    description: str | None = Field(None, description="Package description")
    version: str | None = Field(None, description="Package version")
    models: list[str] = Field(
        default_factory=list, description="List of model paths in the package"
    )


class MalloyModelMetadata(BaseModel):
    """Metadata for a Malloy model."""

    path: str = Field(..., description="Path to the model file")
    description: str | None = Field(None, description="Model description")
    sources: list[str] = Field(
        default_factory=list, description="Available data sources in the model"
    )
    queries: list[str] = Field(
        default_factory=list, description="Named queries defined in the model"
    )
    model_schema: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Schema information for sources"
    )


class MalloyProjectMetadata(BaseModel):
    """Metadata for a Malloy project."""

    name: str = Field(..., description="Project name")
    description: str | None = Field(None, description="Project description")
    packages: list[MalloyPackageMetadata] = Field(
        default_factory=list, description="Available packages in the project"
    )
    models: list[MalloyModelMetadata] = Field(
        default_factory=list, description="Available models in the project"
    )
