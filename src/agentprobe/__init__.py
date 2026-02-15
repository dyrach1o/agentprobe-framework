"""AgentProbe — a testing and evaluation framework for software agents."""

__version__ = "1.1.0"

from agentprobe.core.assertions import expect, expect_tool_calls
from agentprobe.core.chaos import ChaosProxy
from agentprobe.core.conversation import ConversationRunner
from agentprobe.core.scenario import scenario
from agentprobe.core.snapshot import SnapshotManager
from agentprobe.cost.budget import BudgetEnforcer
from agentprobe.eval.statistical import StatisticalEvaluator
from agentprobe.eval.trace_compare import TraceComparisonEvaluator
from agentprobe.metrics.aggregator import MetricAggregator
from agentprobe.metrics.collector import MetricCollector
from agentprobe.metrics.trend import MetricTrend
from agentprobe.plugins.base import PluginBase
from agentprobe.plugins.manager import PluginManager
from agentprobe.plugins.registry import PluginRegistry
from agentprobe.regression.baseline import BaselineManager
from agentprobe.regression.detector import RegressionDetector
from agentprobe.testing import assert_cost, assert_score, assert_trace
from agentprobe.trace.replay import ReplayEngine
from agentprobe.trace.time_travel import TimeTravel

__all__ = [
    "BaselineManager",
    "BudgetEnforcer",
    "ChaosProxy",
    "ConversationRunner",
    "MetricAggregator",
    "MetricCollector",
    "MetricTrend",
    "PluginBase",
    "PluginManager",
    "PluginRegistry",
    "RegressionDetector",
    "ReplayEngine",
    "SnapshotManager",
    "StatisticalEvaluator",
    "TimeTravel",
    "TraceComparisonEvaluator",
    "__version__",
    "assert_cost",
    "assert_score",
    "assert_trace",
    "expect",
    "expect_tool_calls",
    "scenario",
]
