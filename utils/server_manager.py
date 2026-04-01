"""
Server Management Module
========================
Manages the state of 4 phone servers acting as compute nodes.
Handles AI-driven server shutdown decisions and device control.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import subprocess
import platform


@dataclass
class PhoneServer:
    """Represents a single phone server in the infrastructure."""
    id: int
    name: str
    is_active: bool = True
    device_id: Optional[str] = None  # ADB device ID for real control
    
    def toggle(self) -> bool:
        """Toggle server state and return new state."""
        self.is_active = not self.is_active
        return self.is_active


@dataclass
class ShutdownDecision:
    """Result of an AI shutdown decision."""
    should_shutdown: bool
    target_server: Optional[int] = None
    reason: str = ""
    efficiency_gain: float = 0.0


class ServerManager:
    """
    Manages a fleet of 4 phone servers for distributed computing.
    
    Features:
    - Track individual server states (ON/OFF)
    - AI-driven shutdown decisions based on efficiency
    - Optional ADB control for real devices
    - Safe shutdown constraints (minimum 2 servers)
    """
    
    # Minimum servers that must remain active
    MIN_ACTIVE_SERVERS = 2
    
    # Workload threshold for considering shutdown
    WORKLOAD_THRESHOLD = 35.0
    
    # Minimum efficiency gain required to justify shutdown
    MIN_EFFICIENCY_GAIN = 1.0
    
    def __init__(self, device_ids: Optional[List[str]] = None):
        """
        Initialize the server manager with 4 phone servers.
        
        Args:
            device_ids: Optional list of ADB device IDs for real device control
        """
        self.servers: Dict[int, PhoneServer] = {}
        
        # Initialize 4 phone servers
        for i in range(1, 5):
            device_id = device_ids[i-1] if device_ids and len(device_ids) >= i else None
            self.servers[i] = PhoneServer(
                id=i,
                name=f"Phone {i}",
                is_active=True,
                device_id=device_id
            )
        
        # Track shutdown history
        self._shutdown_history: List[Dict] = []
        self._last_action: Optional[str] = None
        
    @property
    def active_count(self) -> int:
        """Get count of currently active servers."""
        return sum(1 for s in self.servers.values() if s.is_active)
    
    @property
    def active_servers(self) -> List[PhoneServer]:
        """Get list of active servers."""
        return [s for s in self.servers.values() if s.is_active]
    
    @property
    def inactive_servers(self) -> List[PhoneServer]:
        """Get list of inactive servers."""
        return [s for s in self.servers.values() if not s.is_active]
    
    def get_server_states(self) -> Dict[int, bool]:
        """
        Get the ON/OFF state of all servers.
        
        Returns:
            Dictionary mapping server ID to active status
        """
        return {s.id: s.is_active for s in self.servers.values()}
    
    def get_server_display(self) -> List[Tuple[str, bool]]:
        """
        Get server information for display purposes.
        
        Returns:
            List of (server_name, is_active) tuples
        """
        return [(s.name, s.is_active) for s in self.servers.values()]
    
    def can_shutdown(self, workload: float) -> bool:
        """
        Check if a server can be safely shut down.
        
        Args:
            workload: Current workload percentage
            
        Returns:
            True if shutdown is possible
        """
        # Must have more than minimum servers
        if self.active_count <= self.MIN_ACTIVE_SERVERS:
            return False
        
        # Workload must be below threshold
        if workload >= self.WORKLOAD_THRESHOLD:
            return False
        
        return True
    
    def decide_shutdown(
        self,
        current_state: Dict[str, float],
        current_efficiency: float,
        predicted_efficiency_after: float
    ) -> ShutdownDecision:
        """
        Decide whether to shut down a server based on AI analysis.
        
        Rules:
        1. Workload must be < 35%
        2. Must have > 2 servers active
        3. Predicted efficiency must increase
        
        Args:
            current_state: Dictionary with 'workload', 'servers', etc.
            current_efficiency: Current efficiency percentage
            predicted_efficiency_after: Predicted efficiency after shutdown
            
        Returns:
            ShutdownDecision with recommendation
        """
        workload = current_state.get('workload', 100)
        active_servers = self.active_count
        
        # Check constraint 1: workload threshold
        if workload >= self.WORKLOAD_THRESHOLD:
            return ShutdownDecision(
                should_shutdown=False,
                reason=f"Workload ({workload:.1f}%) is above threshold ({self.WORKLOAD_THRESHOLD}%)"
            )
        
        # Check constraint 2: minimum servers
        if active_servers <= self.MIN_ACTIVE_SERVERS:
            return ShutdownDecision(
                should_shutdown=False,
                reason=f"Cannot go below {self.MIN_ACTIVE_SERVERS} active servers"
            )
        
        # Check constraint 3: efficiency improvement
        efficiency_gain = predicted_efficiency_after - current_efficiency
        if efficiency_gain < self.MIN_EFFICIENCY_GAIN:
            return ShutdownDecision(
                should_shutdown=False,
                reason=f"Efficiency gain ({efficiency_gain:.1f}%) is insufficient"
            )
        
        # Find a server to shut down (prefer higher numbered servers)
        target_server = None
        for server_id in sorted(self.servers.keys(), reverse=True):
            if self.servers[server_id].is_active:
                target_server = server_id
                break
        
        if target_server is None:
            return ShutdownDecision(
                should_shutdown=False,
                reason="No suitable server found for shutdown"
            )
        
        return ShutdownDecision(
            should_shutdown=True,
            target_server=target_server,
            reason=f"Low workload ({workload:.1f}%) - shutdown will improve efficiency",
            efficiency_gain=efficiency_gain
        )
    
    def execute_shutdown(self, server_id: int, use_adb: bool = False) -> bool:
        """
        Execute server shutdown.
        
        Args:
            server_id: ID of server to shut down
            use_adb: Whether to send real ADB command
            
        Returns:
            True if shutdown successful
        """
        if server_id not in self.servers:
            return False
        
        server = self.servers[server_id]
        
        if not server.is_active:
            return False  # Already off
        
        # Toggle server state
        server.is_active = False
        
        # Record action
        self._last_action = f"AI shut down {server.name} to improve efficiency"
        self._shutdown_history.append({
            'server_id': server_id,
            'action': 'shutdown',
            'reason': 'AI optimization'
        })
        
        # Optionally send real ADB command
        if use_adb and server.device_id:
            self.send_adb_command(server.device_id, 'sleep')
        
        return True
    
    def activate_server(self, server_id: int, use_adb: bool = False) -> bool:
        """
        Activate a server.
        
        Args:
            server_id: ID of server to activate
            use_adb: Whether to send real ADB command
            
        Returns:
            True if activation successful
        """
        if server_id not in self.servers:
            return False
        
        server = self.servers[server_id]
        
        if server.is_active:
            return False  # Already on
        
        server.is_active = True
        
        self._last_action = f"Activated {server.name}"
        
        if use_adb and server.device_id:
            self.send_adb_command(server.device_id, 'wake')
        
        return True
    
    def get_last_action(self) -> Optional[str]:
        """Get the last action performed."""
        return self._last_action
    
    def clear_last_action(self) -> None:
        """Clear the last action message."""
        self._last_action = None
    
    @staticmethod
    def send_adb_command(device_id: str, action: str = 'sleep') -> bool:
        """
        Send ADB command to control a real Android device.
        
        This function can control real phones in production environments.
        In this simulation, it demonstrates the capability but may not
        have real devices connected.
        
        Args:
            device_id: ADB device identifier (e.g., 'emulator-5554' or serial number)
            action: 'sleep' to turn off screen, 'wake' to turn on
            
        Returns:
            True if command was sent successfully
            
        Example usage in production:
            send_adb_command('192.168.1.100:5555', 'sleep')
            
        Common ADB commands:
            - keyevent 26: Power button (toggle screen)
            - keyevent 223: Sleep
            - keyevent 224: Wake up
        """
        # Map actions to key events
        key_events = {
            'sleep': '223',      # KEYCODE_SLEEP
            'wake': '224',       # KEYCODE_WAKEUP
            'toggle': '26',      # KEYCODE_POWER
        }
        
        key_event = key_events.get(action, '26')
        
        # Build ADB command
        command = ['adb', '-s', device_id, 'shell', 'input', 'keyevent', key_event]
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"[ADB] Successfully sent {action} command to {device_id}")
                return True
            else:
                print(f"[ADB] Command failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[ADB] Command timed out for {device_id}")
            return False
        except FileNotFoundError:
            # ADB not installed or not in PATH
            print("[ADB] ADB not found. Install Android SDK tools for real device control.")
            return False
        except Exception as e:
            print(f"[ADB] Error: {e}")
            return False
    
    def reset(self) -> None:
        """Reset all servers to active state."""
        for server in self.servers.values():
            server.is_active = True
        self._last_action = None
        self._shutdown_history.clear()


def create_server_manager(device_ids: Optional[List[str]] = None) -> ServerManager:
    """
    Factory function to create a ServerManager instance.
    
    Args:
        device_ids: Optional list of ADB device IDs
        
    Returns:
        Configured ServerManager instance
    """
    return ServerManager(device_ids)