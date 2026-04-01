"""
Dataset Generation Script - FIXED
==================================
Generates 5000 realistic infrastructure samples using stateful simulation.
Uses corrected efficiency formula for realistic values (20-92% range).

Usage:
    python generate_dataset.py
"""

import os
import numpy as np
import pandas as pd
from typing import List, Dict
import math


class DatasetGenerator:
    """
    Generates realistic infrastructure dataset using time-series behavior.
    Maintains state between samples for realistic transitions.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the dataset generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)
        
        # Simulation state
        self.workload = 50.0
        self.temperature = 30.0
        self.servers = 4
        self.time_step = 0
        
        # For smooth patterns
        self.phase_offset = np.random.uniform(0, 2 * np.pi)
        self.workload_trend = 0.0
        self.trend_duration = 0
        
    def _update_workload(self) -> float:
        """Calculate next workload value using time-series behavior."""
        # Primary daily cycle
        primary_wave = 20 * math.sin(2 * math.pi * self.time_step / 100 + self.phase_offset)
        
        # Secondary hourly variations
        secondary_wave = 10 * math.sin(2 * math.pi * self.time_step / 30)
        
        # Trend drift
        if self.trend_duration <= 0:
            self.workload_trend = np.random.uniform(-0.3, 0.3)
            self.trend_duration = np.random.randint(30, 80)
        self.trend_duration -= 1
        
        # Base workload with patterns
        base = 55 + primary_wave + secondary_wave
        
        # Apply drift
        drift_factor = self.workload_trend * 0.01 * self.time_step
        
        # Small noise
        noise = np.random.normal(0, 2)
        
        # Smooth transition from previous value
        target = base + drift_factor + noise
        new_workload = self.workload * 0.8 + target * 0.2
        
        return np.clip(new_workload, 10, 95)
    
    def _calculate_servers(self, workload: float) -> int:
        """Determine optimal server count based on workload."""
        # Higher workload = more servers needed
        if workload > 75:
            return 4
        elif workload > 55:
            return np.random.choice([3, 4], p=[0.3, 0.7])
        elif workload > 35:
            return np.random.choice([2, 3], p=[0.4, 0.6])
        else:
            return np.random.choice([2, 3], p=[0.7, 0.3])
    
    def _calculate_cpu(self, workload: float) -> float:
        """Calculate CPU based on workload with correlation."""
        # CPU follows workload with small variance
        base_cpu = workload * (0.92 + np.random.uniform(-0.08, 0.08))
        noise = np.random.normal(0, 2)
        return np.clip(base_cpu + noise, 5, 98)
    
    def _calculate_energy(self, servers: int, cpu: float) -> float:
        """Calculate energy consumption."""
        base_energy = servers * 15  # 15W per server
        cpu_energy = cpu * 0.8
        noise = np.random.normal(0, 3)
        return np.clip(base_energy + cpu_energy + noise, 25, 200)
    
    def _calculate_temperature(self, energy: float) -> float:
        """Calculate temperature with thermal dynamics."""
        # Heat from energy
        heat_gen = (energy - 50) * 0.04
        
        # Cooling effect
        cooling = (self.temperature - 25) * 0.06
        
        # Net change
        if heat_gen > cooling:
            temp_change = (heat_gen - cooling) * 0.1
        else:
            temp_change = -cooling * 0.3
        
        new_temp = self.temperature + temp_change
        return np.clip(new_temp, 25, 48)
    
    def _calculate_efficiency(self, workload: float, servers: int, cpu: float, energy: float) -> float:
        """
        Calculate efficiency using a CORRECTED realistic formula.
        
        Efficiency represents how well the infrastructure is being utilized:
        - High workload with few servers = HIGH efficiency (resources well used)
        - Low workload with many servers = LOW efficiency (wasted resources)
        - Optimal is around 70-85% efficiency
        
        Formula considers:
        1. Server utilization (workload per server)
        2. Energy efficiency (work done per watt)
        3. CPU efficiency
        """
        # Base efficiency from server utilization
        # Each server can optimally handle ~30% workload
        optimal_workload_per_server = 30.0
        actual_workload_per_server = workload / servers
        
        # Utilization ratio (how close to optimal)
        utilization_ratio = actual_workload_per_server / optimal_workload_per_server
        
        # Efficiency curve - peaks around utilization_ratio = 1.0
        # Too low = wasted resources, too high = overloaded
        if utilization_ratio <= 1.0:
            # Under-utilized: efficiency scales up
            base_efficiency = utilization_ratio * 85
        else:
            # Over-utilized: efficiency drops due to overhead
            over_ratio = utilization_ratio - 1.0
            base_efficiency = 85 - (over_ratio * 30)
        
        # Energy efficiency bonus/penalty
        expected_energy = servers * 20 + workload * 0.5
        energy_ratio = expected_energy / max(energy, 1)
        energy_factor = np.clip(energy_ratio, 0.8, 1.2)
        
        # CPU efficiency factor
        cpu_efficiency = 1.0 - abs(cpu - workload) / 100 * 0.2
        
        # Combine factors
        efficiency = base_efficiency * energy_factor * cpu_efficiency
        
        # Add slight noise (±2%)
        noise = np.random.normal(0, 2)
        efficiency += noise
        
        # Clip to valid range (20-92%)
        return np.clip(efficiency, 20, 92)
    
    def generate_sample(self) -> Dict[str, float]:
        """Generate a single sample."""
        self.time_step += 1
        
        # Update workload (smooth transition)
        self.workload = self._update_workload()
        
        # Determine servers
        servers = self._calculate_servers(self.workload)
        self.servers = servers
        
        # Calculate other metrics
        cpu = self._calculate_cpu(self.workload)
        energy = self._calculate_energy(servers, cpu)
        self.temperature = self._calculate_temperature(energy)
        efficiency = self._calculate_efficiency(self.workload, servers, cpu, energy)
        
        return {
            'servers': servers,
            'workload': round(self.workload, 2),
            'cpu': round(cpu, 2),
            'energy': round(energy, 2),
            'temperature': round(self.temperature, 2),
            'efficiency': round(efficiency, 2)
        }
    
    def generate_dataset(self, n_samples: int = 5000) -> pd.DataFrame:
        """
        Generate full dataset.
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            DataFrame with all samples
        """
        samples = []
        
        for i in range(n_samples):
            # Occasionally reset to simulate different scenarios
            if i > 0 and i % 1000 == 0:
                self.phase_offset = np.random.uniform(0, 2 * np.pi)
                self.workload = np.random.uniform(30, 70)
                self.temperature = np.random.uniform(28, 35)
            
            sample = self.generate_sample()
            samples.append(sample)
        
        return pd.DataFrame(samples)


def main():
    """Main function to generate and save dataset."""
    print("=" * 60)
    print("AI Infrastructure Dataset Generator (FIXED)")
    print("=" * 60)
    
    # Create dataset directory
    os.makedirs('dataset', exist_ok=True)
    
    # Generate dataset
    print("\n📊 Generating 5000 realistic infrastructure samples...")
    generator = DatasetGenerator(seed=42)
    df = generator.generate_dataset(5000)
    
    # Save to CSV
    output_path = 'dataset/dataset.csv'
    df.to_csv(output_path, index=False)
    print(f"✅ Dataset saved to: {output_path}")
    
    # Display statistics
    print("\n📈 Dataset Statistics:")
    print("-" * 40)
    print(f"Total samples: {len(df)}")
    print(f"\n{df.describe().round(2)}")
    
    # Verify efficiency bounds
    print("\n🔍 Efficiency Validation:")
    print(f"  Min efficiency: {df['efficiency'].min():.2f}%")
    print(f"  Max efficiency: {df['efficiency'].max():.2f}%")
    print(f"  Mean efficiency: {df['efficiency'].mean():.2f}%")
    print(f"  Std efficiency: {df['efficiency'].std():.2f}%")
    
    # Efficiency distribution
    print("\n📊 Efficiency Distribution:")
    bins = [20, 40, 60, 80, 92]
    for i in range(len(bins)-1):
        count = len(df[(df['efficiency'] >= bins[i]) & (df['efficiency'] < bins[i+1])])
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"  {bins[i]:2d}-{bins[i+1]:2d}%: {count:4d} ({pct:5.1f}%) {bar}")
    
    # Check for realistic transitions
    print("\n🔄 Transition Smoothness Check:")
    workload_diff = df['workload'].diff().abs().mean()
    temp_diff = df['temperature'].diff().abs().mean()
    print(f"  Avg workload change: {workload_diff:.2f}%")
    print(f"  Avg temperature change: {temp_diff:.2f}°C")
    
    print("\n✅ Dataset generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()