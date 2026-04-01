"""
Temperature Alarm Module
========================
Provides non-blocking temperature alarm functionality.
Triggers when temperature exceeds safety threshold.
"""

import threading
import time
import os
from typing import Optional, Callable
import wave
import struct
import math


class TemperatureAlarm:
    """
    Non-blocking temperature alarm system.
    
    Features:
    - Triggers at configurable temperature threshold
    - Plays alarm sound for specified duration
    - Uses threading to avoid blocking the UI
    - Auto-generates alarm sound if file not found
    """
    
    DEFAULT_THRESHOLD = 42.0  # Celsius
    DEFAULT_DURATION = 3.0    # Seconds
    
    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        duration: float = DEFAULT_DURATION,
        alarm_file: str = "assets/alarm.mp3"
    ):
        """
        Initialize the temperature alarm.
        
        Args:
            threshold: Temperature threshold in Celsius
            duration: Duration to play alarm in seconds
            alarm_file: Path to alarm sound file
        """
        self.threshold = threshold
        self.duration = duration
        self.alarm_file = alarm_file
        
        self._is_playing = False
        self._alarm_thread: Optional[threading.Thread] = None
        self._last_trigger_time: float = 0
        self._cooldown = 10.0  # Seconds between alarms
        
        # Ensure assets directory exists and create alarm if needed
        self._ensure_alarm_file()
    
    def _ensure_alarm_file(self) -> None:
        """Ensure alarm file exists, create if necessary."""
        # Create assets directory if it doesn't exist
        os.makedirs(os.path.dirname(self.alarm_file) or "assets", exist_ok=True)
        
        # Create a WAV file if MP3 doesn't exist
        wav_file = self.alarm_file.replace('.mp3', '.wav')
        
        if not os.path.exists(self.alarm_file) and not os.path.exists(wav_file):
            self._generate_alarm_wav(wav_file)
            self.alarm_file = wav_file
        elif os.path.exists(wav_file):
            self.alarm_file = wav_file
    
    def _generate_alarm_wav(self, filepath: str) -> None:
        """
        Generate a simple alarm WAV file.
        Creates a two-tone siren effect.
        """
        try:
            sample_rate = 44100
            duration = 3.0
            
            # Generate two-tone alarm
            num_samples = int(sample_rate * duration)
            samples = []
            
            for i in range(num_samples):
                t = i / sample_rate
                
                # Alternate between two frequencies for siren effect
                if int(t * 4) % 2 == 0:
                    freq = 800  # High tone
                else:
                    freq = 600  # Low tone
                
                # Generate sine wave with envelope
                envelope = min(1.0, min(t * 10, (duration - t) * 10))
                sample = int(32767 * envelope * 0.7 * math.sin(2 * math.pi * freq * t))
                samples.append(sample)
            
            # Write WAV file
            with wave.open(filepath, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                
                for sample in samples:
                    wav.writeframes(struct.pack('<h', sample))
            
            print(f"[Alarm] Generated alarm sound: {filepath}")
            
        except Exception as e:
            print(f"[Alarm] Could not generate alarm file: {e}")
    
    def check_and_trigger(self, temperature: float) -> bool:
        """
        Check temperature and trigger alarm if threshold exceeded.
        
        Args:
            temperature: Current temperature in Celsius
            
        Returns:
            True if alarm was triggered, False otherwise
        """
        if temperature >= self.threshold:
            return self.trigger()
        return False
    
    def trigger(self) -> bool:
        """
        Trigger the alarm in a non-blocking manner.
        
        Returns:
            True if alarm was triggered, False if on cooldown
        """
        current_time = time.time()
        
        # Check cooldown
        if current_time - self._last_trigger_time < self._cooldown:
            return False
        
        # Check if already playing
        if self._is_playing:
            return False
        
        self._last_trigger_time = current_time
        
        # Start alarm in separate thread
        self._alarm_thread = threading.Thread(
            target=self._play_alarm,
            daemon=True
        )
        self._alarm_thread.start()
        
        return True
    
    def _play_alarm(self) -> None:
        """Play the alarm sound (runs in separate thread)."""
        self._is_playing = True
        
        try:
            # Try using playsound
            try:
                from playsound import playsound
                if os.path.exists(self.alarm_file):
                    playsound(self.alarm_file, block=True)
                else:
                    self._beep_fallback()
            except ImportError:
                self._beep_fallback()
            except Exception as e:
                print(f"[Alarm] Playsound error: {e}")
                self._beep_fallback()
                
        finally:
            self._is_playing = False
    
    def _beep_fallback(self) -> None:
        """Fallback beep using system methods."""
        import sys
        
        try:
            if sys.platform == 'win32':
                import winsound
                # Play alternating beeps
                for _ in range(3):
                    winsound.Beep(800, 300)
                    winsound.Beep(600, 300)
            else:
                # Unix-like systems
                for _ in range(3):
                    print('\a', end='', flush=True)
                    time.sleep(0.5)
        except Exception:
            # Final fallback - just print
            print("\n🚨 ALARM: TEMPERATURE CRITICAL! 🚨")
    
    def is_playing(self) -> bool:
        """Check if alarm is currently playing."""
        return self._is_playing
    
    def stop(self) -> None:
        """Stop the alarm if playing."""
        self._is_playing = False
    
    def set_threshold(self, threshold: float) -> None:
        """Update the temperature threshold."""
        self.threshold = threshold
    
    def get_status(self, temperature: float) -> str:
        """
        Get the current alarm status.
        
        Args:
            temperature: Current temperature
            
        Returns:
            Status string
        """
        if self._is_playing:
            return "🚨 ALARM ACTIVE"
        elif temperature >= self.threshold:
            return f"⚠️ CRITICAL: {temperature:.1f}°C"
        elif temperature >= self.threshold - 4:
            return f"🟡 WARNING: {temperature:.1f}°C"
        else:
            return f"🟢 NORMAL: {temperature:.1f}°C"


class AlarmManager:
    """
    Manages multiple alarm types for comprehensive monitoring.
    """
    
    def __init__(self):
        """Initialize the alarm manager."""
        self.temperature_alarm = TemperatureAlarm()
        self._callbacks: list[Callable] = []
    
    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback to be called when alarm triggers."""
        self._callbacks.append(callback)
    
    def check_all(
        self,
        temperature: float,
        cpu: Optional[float] = None,
        energy: Optional[float] = None
    ) -> list[str]:
        """
        Check all alarm conditions.
        
        Returns:
            List of triggered alarm messages
        """
        triggered = []
        
        if self.temperature_alarm.check_and_trigger(temperature):
            msg = f"Temperature alarm: {temperature:.1f}°C"
            triggered.append(msg)
            for callback in self._callbacks:
                callback(msg)
        
        return triggered


def create_alarm(
    threshold: float = 42.0,
    duration: float = 3.0
) -> TemperatureAlarm:
    """
    Factory function to create a TemperatureAlarm instance.
    
    Args:
        threshold: Temperature threshold in Celsius
        duration: Alarm duration in seconds
        
    Returns:
        Configured TemperatureAlarm instance
    """
    return TemperatureAlarm(threshold=threshold, duration=duration)