import os
import sys
import subprocess
import time
import base64
from io import BytesIO
from PIL import ImageGrab, Image
import threading

# SUMO configuration
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)

try:
    from linear_rl.true_online_sarsa import TrueOnlineSarsaLambda
    from sumo_rl import cologne8
    import pyautogui  # For taking screenshots
    SUMO_AVAILABLE = True
except ImportError:
    SUMO_AVAILABLE = False


class LiveSimulation:
    """Run SUMO simulation with live screenshots"""
    
    def __init__(self):
        self.is_running = False
        self.screenshots = []
        self.current_episode = 0
        
    def capture_screenshots(self, interval=0.5, duration=60):
        """Capture screenshots at regular intervals"""
        start_time = time.time()
        while self.is_running and (time.time() - start_time) < duration:
            try:
                # Capture screenshot
                screenshot = pyautogui.screenshot()
                
                # Convert to base64 for web transfer
                buffered = BytesIO()
                screenshot.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                self.screenshots.append({
                    'timestamp': time.time(),
                    'image': img_str
                })
                
                # Keep only last 10 screenshots to save memory
                if len(self.screenshots) > 10:
                    self.screenshots.pop(0)
                    
                time.sleep(interval)
            except Exception as e:
                print(f"Screenshot error: {e}")
                
    def run_with_gui(self, episodes=5, alpha=0.00001, gamma=0.95, 
                     epsilon=0.05, lamb=0.1, fourier_order=2):
        """Run simulation with SUMO GUI visible"""
        if not SUMO_AVAILABLE:
            raise Exception("SUMO-RL not available")
        
        self.is_running = True
        
        # Start screenshot capture in background
        screenshot_thread = threading.Thread(
            target=self.capture_screenshots,
            args=(1.0, episodes * 60)  # 1 screenshot per second
        )
        screenshot_thread.start()
        
        try:
            # Create environment with GUI enabled
            output_file = f"outputs/cologne8/live_{int(time.time())}"
            env = cologne8(
                out_csv_name=output_file, 
                use_gui=True,  # Enable GUI!
                yellow_time=2, 
                fixed_ts=False
            )
            env.reset()
            
            # Create agents
            agents = {
                ts_id: TrueOnlineSarsaLambda(
                    env.observation_spaces[ts_id],
                    env.action_spaces[ts_id],
                    alpha=alpha,
                    gamma=gamma,
                    epsilon=epsilon,
                    lamb=lamb,
                    fourier_order=fourier_order,
                )
                for ts_id in env.agents
            }
            
            # Run episodes
            for ep in range(1, episodes + 1):
                self.current_episode = ep
                obs, _ = env.reset()
                
                while env.agents:
                    actions = {ts_id: agents[ts_id].act(obs[ts_id]) for ts_id in obs.keys()}
                    next_obs, r, terminated, truncated, _ = env.step(actions=actions)
                    
                    for ts_id in next_obs.keys():
                        agents[ts_id].learn(
                            state=obs[ts_id],
                            action=actions[ts_id],
                            reward=r[ts_id],
                            next_state=next_obs[ts_id],
                            done=terminated[ts_id],
                        )
                        obs[ts_id] = next_obs[ts_id]
            
            env.close()
            
        finally:
            self.is_running = False
            screenshot_thread.join()
    
    def get_latest_screenshot(self):
        """Get the most recent screenshot"""
        if self.screenshots:
            return self.screenshots[-1]
        return None


live_sim = LiveSimulation()
