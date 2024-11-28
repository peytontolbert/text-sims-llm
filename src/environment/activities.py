from dataclasses import dataclass
from typing import Dict, Optional, Callable
from src.utils.constants import ActivityState, ActivityType
import time

@dataclass
class Activity:
    type: ActivityType
    start_time: float
    duration: float  # in seconds
    need_changes: Dict[str, float]  # per second changes
    exit_condition: Optional[Callable[['Activity'], bool]] = None
    state: ActivityState = ActivityState.BUSY

class ActivityManager:
    def __init__(self):
        self.current_activity: Optional[Activity] = None
        
    def start_activity(self, activity_type: ActivityType, duration: float, need_changes: Dict[str, float], 
                      exit_condition: Optional[Callable[['Activity'], bool]] = None) -> bool:
        if self.current_activity and self.current_activity.state != ActivityState.NEEDS_EXIT:
            return False
            
        self.current_activity = Activity(
            type=activity_type,
            start_time=time.time(),
            duration=duration,
            need_changes=need_changes,
            exit_condition=exit_condition
        )
        return True
    
    def exit_activity(self) -> bool:
        if not self.current_activity or self.current_activity.state != ActivityState.NEEDS_EXIT:
            return False
        self.current_activity = None
        return True
    
    def update(self, needs: Dict[str, float]) -> Dict[str, float]:
        if not self.current_activity:
            return needs
            
        elapsed_time = time.time() - self.current_activity.start_time
        
        # Check if activity should end
        if elapsed_time >= self.current_activity.duration:
            self.current_activity.state = ActivityState.NEEDS_EXIT
            
        # Check custom exit condition
        if (self.current_activity.exit_condition and 
            self.current_activity.exit_condition(self.current_activity)):
            self.current_activity.state = ActivityState.NEEDS_EXIT
            
        # Apply need changes if activity is ongoing
        if self.current_activity.state == ActivityState.BUSY:
            for need, change_per_second in self.current_activity.need_changes.items():
                if need in needs:
                    needs[need] += change_per_second
                    
        return needs
    
    @property
    def is_busy(self) -> bool:
        return self.current_activity is not None and self.current_activity.state == ActivityState.BUSY
    
    @property
    def needs_exit(self) -> bool:
        return self.current_activity is not None and self.current_activity.state == ActivityState.NEEDS_EXIT 