"""Typed errors for the AI visual engine.

Using specific exception types lets the report orchestrator (report.py) catch
failures per-visual and recover, instead of letting one bad visual crash the
whole request (requirement #15).
"""


class AiReportError(Exception):
    """Base class for all engine errors."""


class DataLoadError(AiReportError):
    """Raised when a dataset cannot be loaded."""


class SchemaError(AiReportError):
    """The visual/report plan does not match the expected JSON structure."""


class SemanticError(AiReportError):
    """The plan references a dataset/column/measure that does not exist,
    or uses it in an invalid way (e.g. aggregating a non-numeric column)."""


class DateParseError(AiReportError):
    """A column could not be reliably interpreted as a date."""


class VisualError(AiReportError):
    """A single visual failed to build or render."""


class ExpressionError(AiReportError):
    """A calculated-measure expression is invalid or references unknown columns."""
