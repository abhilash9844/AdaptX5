"""
AI Optimizer Module - FIXED
===========================
Provides intelligent suggestions for infrastructure optimization.
Fixed to return proper suggestion messages.
"""

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class SuggestionPriority(Enum):
    """Priority levels for optimization suggestions."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class OptimizationSuggestion:
    """Represents a single optimization suggestion."""
    message: str
    priority: SuggestionPriority
    category: str
    action_type: str  # 'automated' or 'manual'
    icon: str = ""    # Emoji icon for display
    
    def get_display_text(self) -> str:
        """Get formatted display text."""
        return f"{self.icon} {self.message}" if self.icon else self.message
    
    def __str__(self) -> str:
        return f"[{self.priority.name}] {self.message}"


class AIOptimizer:
    """
    AI-powered infrastructure optimizer.
    
    Analyzes system state and provides actionable suggestions.
    """
    
    # Thresholds for analysis
    TEMP_WARNING = 38.0
    TEMP_CRITICAL = 42.0
    WORKLOAD_LOW = 30.0
    WORKLOAD_HIGH = 75.0
    WORKLOAD_CRITICAL = 90.0
    CPU_HIGH = 80.0
    CPU_CRITICAL = 95.0
    EFFICIENCY_LOW = 45.0
    EFFICIENCY_GOOD = 60.0
    EFFICIENCY_EXCELLENT = 75.0
    ENERGY_HIGH = 120.0
    
    def __init__(self):
        """Initialize the AI optimizer."""
        self._suggestion_history: List[OptimizationSuggestion] = []
        
    def analyze(
        self,
        servers: int,
        workload: float,
        cpu: float,
        energy: float,
        temperature: float,
        efficiency: float
    ) -> List[OptimizationSuggestion]:
        """
        Analyze current infrastructure state and generate suggestions.
        """
        suggestions = []
        
        # Temperature Analysis (Safety Critical)
        suggestions.extend(self._analyze_temperature(temperature))
        
        # Workload Analysis
        suggestions.extend(self._analyze_workload(workload, servers))
        
        # CPU Analysis
        suggestions.extend(self._analyze_cpu(cpu))
        
        # Energy Analysis
        suggestions.extend(self._analyze_energy(energy, servers))
        
        # Efficiency Analysis
        suggestions.extend(self._analyze_efficiency(efficiency, workload, servers))
        
        # Server Utilization Analysis
        suggestions.extend(self._analyze_server_utilization(servers, workload, efficiency))
        
        # If no issues found, system is stable
        if not suggestions:
            suggestions.append(OptimizationSuggestion(
                message="System operating at optimal efficiency - no changes needed",
                priority=SuggestionPriority.INFO,
                category="status",
                action_type="none",
                icon="✅"
            ))
        
        # Sort by priority
        suggestions.sort(key=lambda x: x.priority.value)
        
        # Store in history
        self._suggestion_history = suggestions
        
        return suggestions
    
    def _analyze_temperature(self, temperature: float) -> List[OptimizationSuggestion]:
        """Analyze temperature and generate cooling suggestions."""
        suggestions = []
        
        if temperature >= self.TEMP_CRITICAL:
            suggestions.append(OptimizationSuggestion(
                message=f"CRITICAL: Temperature at {temperature:.1f}°C exceeds safe limit! Activate emergency cooling immediately",
                priority=SuggestionPriority.CRITICAL,
                category="temperature",
                action_type="manual",
                icon="🚨"
            ))
            suggestions.append(OptimizationSuggestion(
                message="Increase cooling system capacity to maximum output",
                priority=SuggestionPriority.CRITICAL,
                category="temperature",
                action_type="manual",
                icon="💨"
            ))
        elif temperature >= self.TEMP_WARNING:
            suggestions.append(OptimizationSuggestion(
                message=f"Temperature elevated at {temperature:.1f}°C - monitor closely",
                priority=SuggestionPriority.HIGH,
                category="temperature",
                action_type="manual",
                icon="⚠️"
            ))
            suggestions.append(OptimizationSuggestion(
                message="Consider increasing cooling or reducing workload to prevent overheating",
                priority=SuggestionPriority.HIGH,
                category="temperature",
                action_type="manual",
                icon="💨"
            ))
            
        return suggestions
    
    def _analyze_workload(self, workload: float, servers: int) -> List[OptimizationSuggestion]:
        """Analyze workload and generate distribution suggestions."""
        suggestions = []
        
        if workload >= self.WORKLOAD_CRITICAL:
            suggestions.append(OptimizationSuggestion(
                message=f"Critical workload level at {workload:.1f}% - system may become unstable",
                priority=SuggestionPriority.CRITICAL,
                category="workload",
                action_type="manual",
                icon="🔴"
            ))
            if servers < 4:
                suggestions.append(OptimizationSuggestion(
                    message=f"Activate additional servers to distribute load (currently {servers}/4 active)",
                    priority=SuggestionPriority.HIGH,
                    category="workload",
                    action_type="manual",
                    icon="➕"
                ))
        elif workload >= self.WORKLOAD_HIGH:
            suggestions.append(OptimizationSuggestion(
                message=f"High workload detected at {workload:.1f}% - consider load balancing",
                priority=SuggestionPriority.MEDIUM,
                category="workload",
                action_type="manual",
                icon="🟡"
            ))
        elif workload <= self.WORKLOAD_LOW and servers > 2:
            suggestions.append(OptimizationSuggestion(
                message=f"Low workload ({workload:.1f}%) with {servers} servers - consolidation recommended",
                priority=SuggestionPriority.LOW,
                category="workload",
                action_type="automated",
                icon="📉"
            ))
            
        return suggestions
    
    def _analyze_cpu(self, cpu: float) -> List[OptimizationSuggestion]:
        """Analyze CPU usage and generate suggestions."""
        suggestions = []
        
        if cpu >= self.CPU_CRITICAL:
            suggestions.append(OptimizationSuggestion(
                message=f"CPU usage critically high at {cpu:.1f}% - performance degradation likely",
                priority=SuggestionPriority.CRITICAL,
                category="cpu",
                action_type="manual",
                icon="🔴"
            ))
            suggestions.append(OptimizationSuggestion(
                message="Implement load balancing or terminate non-essential processes",
                priority=SuggestionPriority.HIGH,
                category="cpu",
                action_type="manual",
                icon="⚡"
            ))
        elif cpu >= self.CPU_HIGH:
            suggestions.append(OptimizationSuggestion(
                message=f"CPU usage elevated at {cpu:.1f}% - monitor for further increases",
                priority=SuggestionPriority.MEDIUM,
                category="cpu",
                action_type="manual",
                icon="🟡"
            ))
            
        return suggestions
    
    def _analyze_energy(self, energy: float, servers: int) -> List[OptimizationSuggestion]:
        """Analyze energy consumption and generate suggestions."""
        suggestions = []
        
        energy_per_server = energy / max(servers, 1)
        
        if energy >= self.ENERGY_HIGH:
            suggestions.append(OptimizationSuggestion(
                message=f"High energy consumption at {energy:.1f}W - review power optimization",
                priority=SuggestionPriority.MEDIUM,
                category="energy",
                action_type="manual",
                icon="⚡"
            ))
            suggestions.append(OptimizationSuggestion(
                message="Enable power-saving modes on idle components",
                priority=SuggestionPriority.LOW,
                category="energy",
                action_type="manual",
                icon="🔋"
            ))
            
        if energy_per_server > 40:
            suggestions.append(OptimizationSuggestion(
                message=f"High per-server energy consumption: {energy_per_server:.1f}W per server",
                priority=SuggestionPriority.LOW,
                category="energy",
                action_type="manual",
                icon="📊"
            ))
            
        return suggestions
    
    def _analyze_efficiency(
        self,
        efficiency: float,
        workload: float,
        servers: int
    ) -> List[OptimizationSuggestion]:
        """Analyze efficiency and generate improvement suggestions."""
        suggestions = []
        
        if efficiency < self.EFFICIENCY_LOW:
            suggestions.append(OptimizationSuggestion(
                message=f"Low efficiency at {efficiency:.1f}% - resources are being underutilized",
                priority=SuggestionPriority.HIGH,
                category="efficiency",
                action_type="manual",
                icon="📉"
            ))
            
            if servers > 2 and workload < 50:
                suggestions.append(OptimizationSuggestion(
                    message=f"Consider reducing active servers from {servers} - workload only {workload:.1f}%",
                    priority=SuggestionPriority.MEDIUM,
                    category="efficiency",
                    action_type="automated",
                    icon="🔧"
                ))
                
        elif efficiency >= self.EFFICIENCY_EXCELLENT:
            suggestions.append(OptimizationSuggestion(
                message=f"Excellent efficiency at {efficiency:.1f}% - optimal resource utilization",
                priority=SuggestionPriority.INFO,
                category="efficiency",
                action_type="none",
                icon="🌟"
            ))
        elif efficiency >= self.EFFICIENCY_GOOD:
            suggestions.append(OptimizationSuggestion(
                message=f"Good efficiency at {efficiency:.1f}% - system performing well",
                priority=SuggestionPriority.INFO,
                category="efficiency",
                action_type="none",
                icon="✅"
            ))
            
        return suggestions
    
    def _analyze_server_utilization(
        self,
        servers: int,
        workload: float,
        efficiency: float
    ) -> List[OptimizationSuggestion]:
        """Analyze server utilization patterns."""
        suggestions = []
        
        # Calculate ideal server count
        workload_per_server = workload / max(servers, 1)
        
        if workload_per_server < 15 and servers > 2:
            suggestions.append(OptimizationSuggestion(
                message=f"Servers underutilized at {workload_per_server:.1f}% each - reduce server count",
                priority=SuggestionPriority.LOW,
                category="utilization",
                action_type="automated",
                icon="💡"
            ))
        elif workload_per_server > 35 and servers < 4:
            suggestions.append(OptimizationSuggestion(
                message=f"Servers heavily loaded at {workload_per_server:.1f}% each - consider adding capacity",
                priority=SuggestionPriority.MEDIUM,
                category="utilization",
                action_type="manual",
                icon="💡"
            ))
            
        return suggestions
    
    def get_summary(self) -> str:
        """Get a summary of the current optimization status."""
        if not self._suggestion_history:
            return "No analysis performed yet"
        
        critical = sum(1 for s in self._suggestion_history if s.priority == SuggestionPriority.CRITICAL)
        high = sum(1 for s in self._suggestion_history if s.priority == SuggestionPriority.HIGH)
        
        if critical > 0:
            return f"🚨 {critical} critical issue(s) require immediate attention"
        elif high > 0:
            return f"⚠️ {high} high priority suggestion(s)"
        else:
            return "✅ System operating normally"


def create_optimizer() -> AIOptimizer:
    """Factory function to create an AIOptimizer instance."""
    return AIOptimizer()