"""
Response layer for anomaly detection.

Takes action when anomalies are detected.
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from dataclasses import asdict

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of response actions."""
    ROUTING_OVERRIDE = "routing_override"
    RETRY_STRATEGY = "retry_strategy"
    CIRCUIT_BREAK = "circuit_break"
    LOG_AND_ALERT = "log_and_alert"
    LEARNING_LOOP = "learning_loop"
    NONE = "none"


@dataclass
class AnomalyResponse:
    """Response to an anomaly."""
    anomaly_type: str
    severity: str
    actions: List[Dict[str, Any]]
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.anomaly_type,
            "severity": self.severity,
            "actions": self.actions,
            "message": self.message,
            "metadata": self.metadata,
        }


class ResponseEngine:
    """
    Engine for responding to detected anomalies.
    
    Actions include:
    - Routing override (avoid bad model)
    - Retry strategy (switch model, reduce complexity)
    - Circuit breaker (disable failing model)
    - Logging + feedback
    - Learning loop (feed into training data)
    """
    
    def __init__(self):
        """Initialize response engine."""
        self.handlers: Dict[ActionType, List[Callable]] = {
            action_type: [] for action_type in ActionType
        }
        self.action_history: List[AnomalyResponse] = []
    
    def respond(self, anomaly: Any) -> AnomalyResponse:
        """
        Respond to an anomaly.
        
        Args:
            anomaly: AnomalyResult
            
        Returns:
            Response actions taken
        """
        logger.info(f"Responding to anomaly: {anomaly.anomaly_type}")
        
        actions = []
        
        if hasattr(anomaly, 'anomaly_type'):
            anomaly_type = anomaly.anomaly_type
        else:
            anomaly_type = "unknown"
        
        if hasattr(anomaly, 'severity'):
            severity = anomaly.severity
        else:
            severity = "low"
        
        anomaly_value = anomaly_type.value if hasattr(anomaly_type, 'value') else str(anomaly_type)
        severity_value = severity.value if hasattr(severity, 'value') else str(severity)
        
        if anomaly_value == "latency":
            actions.extend(self._handle_latency_anomaly(anomaly))
        elif anomaly_value == "performance":
            actions.extend(self._handle_performance_anomaly(anomaly))
        elif anomaly_value == "failure":
            actions.extend(self._handle_failure_anomaly(anomaly))
        elif anomaly_value == "routing":
            actions.extend(self._handle_routing_anomaly(anomaly))
        else:
            actions.extend(self._handle_generic_anomaly(anomaly))
        
        if not actions:
            actions.append({
                "type": ActionType.LOG_AND_ALERT.value,
                "details": "Anomaly logged for review"
            })
        
        response = AnomalyResponse(
            anomaly_type=anomaly_value,
            severity=severity_value,
            actions=actions,
            message=f"Detected {anomaly_value} anomaly with {severity_value} severity",
            metadata=anomaly.context if hasattr(anomaly, 'context') else {},
        )
        
        self.action_history.append(response)
        self._execute_handlers(response)
        
        return response
    
    def _handle_latency_anomaly(self, anomaly: Any) -> List[Dict[str, Any]]:
        """Handle latency anomaly."""
        actions = []
        
        severity_value = anomaly.severity.value if hasattr(anomaly.severity, 'value') else "low"
        
        if severity_value in ["high", "critical"]:
            actions.append({
                "type": ActionType.ROUTING_OVERRIDE.value,
                "action": "avoid_model",
                "model": anomaly.context.get("model", "unknown"),
                "reason": f"High latency detected: z={anomaly.z_score:.2f}"
            })
            
            actions.append({
                "type": ActionType.RETRY_STRATEGY.value,
                "action": "switch_model",
                "fallback_to": "faster_model",
                "reduce_complexity": True
            })
        
        actions.append({
            "type": ActionType.LOG_AND_ALERT.value,
            "alert_level": "warning" if severity_value == "high" else "critical",
            "metric": "latency",
            "value": anomaly.value,
            "z_score": round(anomaly.z_score, 3)
        })
        
        return actions
    
    def _handle_performance_anomaly(self, anomaly: Any) -> List[Dict[str, Any]]:
        """Handle performance anomaly (score drop)."""
        actions = []
        
        actions.append({
            "type": ActionType.ROUTING_OVERRIDE.value,
            "action": "deprioritize_model",
            "model": anomaly.context.get("model", "unknown"),
            "reason": f"Performance drop detected: score={anomaly.value}"
        })
        
        actions.append({
            "type": ActionType.LEARNING_LOOP.value,
            "action": "log_for_retraining",
            "context": anomaly.context,
            "metric": "score",
            "value": anomaly.value
        })
        
        return actions
    
    def _handle_failure_anomaly(self, anomaly: Any) -> List[Dict[str, Any]]:
        """Handle failure anomaly."""
        actions = []
        
        actions.append({
            "type": ActionType.CIRCUIT_BREAK.value,
            "action": "disable_temporarily",
            "component": anomaly.context.get("model", "unknown"),
            "duration_seconds": 300,
            "reason": "Repeated failures detected"
        })
        
        actions.append({
            "type": ActionType.RETRY_STRATEGY.value,
            "action": "fallback",
            "fallback_to": "backup_model"
        })
        
        return actions
    
    def _handle_routing_anomaly(self, anomaly: Any) -> List[Dict[str, Any]]:
        """Handle routing anomaly (fallback loops)."""
        actions = []
        
        actions.append({
            "type": ActionType.CIRCUIT_BREAK.value,
            "action": "halt_fallback_loop",
            "reason": "Fallback loop detected",
            "lock_routing": True
        })
        
        actions.append({
            "type": ActionType.LOG_AND_ALERT.value,
            "alert_level": "critical",
            "issue": "routing_loop",
            "path": anomaly.context.get("routing_path", [])
        })
        
        return actions
    
    def _handle_generic_anomaly(self, anomaly: Any) -> List[Dict[str, Any]]:
        """Handle generic anomaly."""
        return [{
            "type": ActionType.LOG_AND_ALERT.value,
            "alert_level": "info",
            "metric": anomaly.metric,
            "value": anomaly.value,
            "z_score": round(anomaly.z_score, 3) if hasattr(anomaly, 'z_score') else 0
        }]
    
    def register_handler(
        self,
        action_type: ActionType,
        handler: Callable[[AnomalyResponse], None],
    ) -> None:
        """
        Register a handler for an action type.
        
        Args:
            action_type: Type of action
            handler: Handler function
        """
        self.handlers[action_type].append(handler)
        logger.info(f"Registered handler for {action_type.value}")
    
    def _execute_handlers(self, response: AnomalyResponse) -> None:
        """Execute registered handlers."""
        for action in response.actions:
            action_type_str = action.get("type", "")
            try:
                action_type = ActionType(action_type_str)
                for handler in self.handlers.get(action_type, []):
                    try:
                        handler(response)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
            except ValueError:
                pass
    
    def get_action_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent action history."""
        return [r.to_dict() for r in self.action_history[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get response statistics."""
        action_counts: Dict[str, int] = {}
        for response in self.action_history:
            for action in response.actions:
                action_type = action.get("type", "unknown")
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        return {
            "total_responses": len(self.action_history),
            "action_counts": action_counts,
            "recent_actions": len(self.action_history[-10:]),
        }
