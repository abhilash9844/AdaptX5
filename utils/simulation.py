"""
Infrastructure Simulation Engine - FIXED
=========================================
Provides realistic, stateful simulation of server infrastructure.
Uses corrected efficiency calculation for realistic values.
"""

import numpy as np
from typing import Dict, Tuple
import math


class InfrastructureSimulator:
    """
    Simulates a realistic infrastructure environment with 4 phone servers.
    
    Key Features:
    - Stateful simulation (previous values influence current)
    - Smooth workload transitions using sine waves and gradual drift
    - Realistic temperature dynamics with heating/cooling effects
    - CORRECTED efficiency calculation producing 20-92% range
    """
    
    # Configuration constants
    BASE_ENERGY_PER_SERVER = 15.0  # Watts per active server
    CPU_ENERGY_FACTOR = 0.8        # Energy multiplier for CPU usage
    TEMP_AMBIENT = 25.0            # Ambient temperature in Celsius
    TEMP_HEATING_RATE = 0.15       # How fast temperature rises
    TEMP_COOLING_RATE = 0.08       # How fast temperature falls
    MAX_TEMPERATURE = 50.0         # Maximum possible temperature
    WORKLOAD_DRIFT_RATE = 0.02     # How fast workload drifts
    
    def __init__(self, initial_servers: int = 4):
        """
        Initialize the infrastructure simulator.
        
        Args:
            initial_servers: Number of servers to start with (1-4)
        """
        # Validate input
        self.servers = max(1, min(4, initial_servers))
        
        # Internal state variables
        self._time_step = 0
        self._workload = 50.0  # Start at 50% workload
        self._temperature = 30.0  # Start at 30°C
        self._workload_trend = 0.0  # Trend direction for workload
        self._trend_duration = 0  # How long current trend lasts
        
        # For smooth oscillation patterns
        self._phase_offset = np.random.uniform(0, 2 * np.pi)
        
        # History for smoothing
        self._cpu_history = [50.0] * 5
        self._energy_history = [100.0] * 5
        
    def _calculate_workload(self) -> float:
        """
        Calculate workload using time-series behavior.
        Combines sine wave patterns with gradual drift for realism.
        """
        # Base oscillation pattern (simulates daily usage patterns)
        primary_wave = 20 * math.sin(2 * math.pi * self._time_step / 50 + self._phase_offset)
        
        # Secondary faster oscillation (simulates hourly variations)
        secondary_wave = 8 * math.sin(2 * math.pi * self._time_step / 15 + self._phase_offset * 0.5)
        
        # Gradual trend drift
        if self._trend_duration <= 0:
            self._workload_trend = np.random.uniform(-0.5, 0.5)
            self._trend_duration = np.random.randint(20, 60)
        
        self._trend_duration -= 1
        
        # Apply drift gradually
        drift = self._workload_trend * self.WORKLOAD_DRIFT_RATE * self._time_step
        
        # Combine all components
        base_workload = 55 + primary_wave + secondary_wave + drift
        
        # Add very small noise (±2%)
        noise = np.random.normal(0, 1)
        
        # Calculate new workload with momentum
        target_workload = base_workload + noise
        new_workload = self._workload * 0.85 + target_workload * 0.15
        
        # Clamp to valid range
        return max(10.0, min(95.0, new_workload))
    
    def _calculate_cpu(self, workload: float) -> float:
        """
        Calculate CPU usage based on workload with realistic correlation.
        """
        base_cpu = workload * (0.95 + np.random.uniform(-0.05, 0.05))
        noise = np.random.normal(0, 1.5)
        
        self._cpu_history.pop(0)
        self._cpu_history.append(base_cpu + noise)
        
        smoothed_cpu = sum(self._cpu_history) / len(self._cpu_history)
        
        return max(5.0, min(98.0, smoothed_cpu))
    
    def _calculate_energy(self, cpu: float) -> float:
        """
        Calculate energy consumption based on active servers and CPU usage.
        """
        base_energy = self.servers * self.BASE_ENERGY_PER_SERVER
        cpu_energy = cpu * self.CPU_ENERGY_FACTOR
        
        total_energy = base_energy + cpu_energy
        fluctuation = np.random.normal(0, 2)
        
        self._energy_history.pop(0)
        self._energy_history.append(total_energy + fluctuation)
        
        smoothed_energy = sum(self._energy_history) / len(self._energy_history)
        
        return max(20.0, min(200.0, smoothed_energy))
    
    def _calculate_temperature(self, energy: float) -> float:
        """
        Calculate temperature with realistic thermal dynamics.
        """
        heat_generation = (energy - 50) * 0.05
        cooling_effect = (self._temperature - self.TEMP_AMBIENT) * self.TEMP_COOLING_RATE
        
        if heat_generation > cooling_effect:
            temp_change = (heat_generation - cooling_effect) * self.TEMP_HEATING_RATE
        else:
            temp_change = -cooling_effect * 0.5
        
        new_temp = self._temperature + temp_change
        
        return max(self.TEMP_AMBIENT, min(self.MAX_TEMPERATURE, new_temp))
    
    def _calculate_efficiency(self, workload: float, cpu: float, energy: float) -> float:
        """
        Calculate efficiency using CORRECTED realistic formula.
        
        Efficiency represents infrastructure utilization:
        - High workload with few servers = HIGH efficiency
        - Low workload with many servers = LOW efficiency
        - Returns values between 20% and 92%
        """
        # Optimal workload per server is around 30%
        optimal_workload_per_server = 30.0
        actual_workload_per_server = workload / max(self.servers, 1)
        
        # Utilization ratio
        utilization_ratio = actual_workload_per_server / optimal_workload_per_server
        
        # Efficiency curve
        if utilization_ratio <= 1.0:
            # Under-utilized: efficiency scales up
            base_efficiency = utilization_ratio * 85
        else:
            # Over-utilized: efficiency drops due to overhead
            over_ratio = min(utilization_ratio - 1.0, 1.0)
            base_efficiency = 85 - (over_ratio * 25)
        
        # Energy efficiency factor
        expected_energy = self.servers * 20 + workload * 0.5
        energy_ratio = expected_energy / max(energy, 1)
        energy_factor = max(0.85, min(1.15, energy_ratio))
        
        # CPU efficiency factor
        cpu_diff = abs(cpu - workload)
        cpu_factor = 1.0 - (cpu_diff / 100) * 0.15
        
        # Combine factors
        efficiency = base_efficiency * energy_factor * cpu_factor
        
        # Small noise
        noise = np.random.normal(0, 1.5)
        efficiency += noise
        
        # Clip to valid range (NEVER exceed 92%)
        return max(20.0, min(92.0, efficiency))
    
    def step(self) -> Dict[str, float]:
        """
        Advance simulation by one time step and return current state.
        """
        self._time_step += 1
        
        # Calculate all metrics
        self._workload = self._calculate_workload()
        cpu = self._calculate_cpu(self._workload)
        energy = self._calculate_energy(cpu)
        self._temperature = self._calculate_temperature(energy)
        efficiency = self._calculate_efficiency(self._workload, cpu, energy)
        
        return {
            'servers': self.servers,
            'workload': round(self._workload, 2),
            'cpu': round(cpu, 2),
            'energy': round(energy, 2),
            'temperature': round(self._temperature, 2),
            'efficiency': round(efficiency, 2)
        }
    
    def get_state(self) -> Tuple[int, float, float, float, float]:
        """Get current state as a tuple."""
        state = self.step()
        return (
            state['servers'],
            state['workload'],
            state['cpu'],
            state['energy'],
            state['temperature']
        )
    
    def set_servers(self, count: int) -> None:
        """Set the number of active servers."""
        self.servers = max(1, min(4, count))
    
    def reduce_servers(self) -> bool:
        """Reduce server count by 1 if possible."""
        if self.servers > 1:
            self.servers -= 1
            return True
        return False
    
    def add_server(self) -> bool:
        """Add a server if possible."""
        if self.servers < 4:
            self.servers += 1
            return True
        return False
    
    def reset(self) -> None:
        """Reset simulation to initial state."""
        self._time_step = 0
        self._workload = 50.0
        self._temperature = 30.0
        self.servers = 4
        self._workload_trend = 0.0
        self._trend_duration = 0
        self._cpu_history = [50.0] * 5
        self._energy_history = [100.0] * 5
        self._phase_offset = np.random.uniform(0, 2 * np.pi)


def create_simulator(initial_servers: int = 4) -> InfrastructureSimulator:
    """Factory function to create an InfrastructureSimulator instance."""
    return InfrastructureSimulator(initial_servers)