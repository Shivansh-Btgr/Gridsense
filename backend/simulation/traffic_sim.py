import os
import sys
import json
from datetime import datetime
import threading
import pandas as pd

# SUMO configuration
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    # Try common installation paths
    possible_paths = [
        r"C:\Program Files (x86)\Eclipse\Sumo",
        r"C:\Program Files\Eclipse\Sumo",
        "/usr/share/sumo",
        "/usr/local/share/sumo"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            os.environ["SUMO_HOME"] = path
            tools = os.path.join(path, "tools")
            sys.path.append(tools)
            break

try:
    from backend.agents.sarsa_lambda import TrueOnlineSarsaLambda
    from backend.simulation.network_mgr import network_manager
    from sumo_rl import SumoEnvironment
    SUMO_AVAILABLE = True
except ImportError:
    SUMO_AVAILABLE = False
    print("Warning: SUMO-RL not properly configured. Traffic simulation will not be available.")


class TrafficSimulation:
    """Wrapper for SUMO traffic simulation with RL optimization"""
    
    def __init__(self):
        self.results = None
        self.is_running = False
        self.progress = 0
        
    def run_simulation(self, episodes=50, use_gui=False, alpha=0.00001, gamma=0.95, 
                      epsilon=0.05, lamb=0.1, fourier_order=3, scenario='cologne8', 
                      num_seconds=1000, callback=None):
        """
        Run traffic signal optimization simulation
        
        Args:
            episodes: Number of training episodes
            use_gui: Whether to show SUMO GUI (not recommended for web)
            alpha: Learning rate
            gamma: Discount factor
            epsilon: Exploration rate
            lamb: Lambda for eligibility traces
            fourier_order: Order of Fourier basis functions (2-4 recommended)
            scenario: Network scenario to use (cologne8, cologne1, etc.)
            num_seconds: Simulation duration per episode in seconds (default: 1000 = ~16 min)
            callback: Function to call with progress updates
        """
        if not SUMO_AVAILABLE:
            raise Exception("SUMO-RL is not properly installed or configured")
        
        # Limit parameters to safe ranges
        fourier_order = min(max(fourier_order, 1), 3)  # 1-3 only for safety
        episodes = min(max(episodes, 1), 200)
        
        self.is_running = True
        self.progress = 0
        
        try:
            # Create output directory
            output_dir = f"outputs/{scenario}"
            os.makedirs(output_dir, exist_ok=True)
            output_file = f"{output_dir}/simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            print(f"Starting simulation with {episodes} episodes, Fourier order: {fourier_order}")
            print(f"Using scenario: {scenario}")
            
            # Initialize environment using network manager
            env = network_manager.create_environment(
                scenario,
                out_csv_name=output_file,
                use_gui=use_gui,
                begin_time=25200,  # Start simulation at 7:00 AM (25200s) when vehicles appear
                num_seconds=num_seconds,  # Control episode length
                yellow_time=2,
                fixed_ts=False,
                reward_fn='diff-waiting-time'  # Use diff in waiting time as reward
            )
            
            # Reset returns just observations (dict) for multi-agent
            obs = env.reset()
            
            # Get traffic signal IDs (available after reset)
            ts_ids = env.ts_ids
            print(f"Environment initialized. Traffic signals: {ts_ids}")
            print(f"Episode duration: {num_seconds}s = max {num_seconds//5} steps per episode")
            
            # Create RL agents for each traffic signal
            agents = {}
            for ts_id in ts_ids:
                print(f"Creating agent for {ts_id}")
                # Get the observation and action spaces (pass ts_id to methods)
                obs_space = env.observation_spaces(ts_id)
                action_space = env.action_spaces(ts_id)
                print(f"  Observation space: {obs_space}")
                print(f"  Action space: {action_space}")
                
                agents[ts_id] = TrueOnlineSarsaLambda(
                    obs_space,
                    action_space,
                    alpha=alpha,
                    gamma=gamma,
                    epsilon=epsilon,
                    lamb=lamb,
                    fourier_order=fourier_order,
                )
                print(f"  Agent created with {agents[ts_id].n_features} features")
            
            print("All agents created successfully")
            
            # Training metrics
            episode_rewards = []
            episode_wait_times = []
            episode_speeds = []
            
            print("All agents created successfully")
            
            # Training metrics
            episode_rewards = []
            
            # Run episodes
            for ep in range(1, episodes + 1):
                if ep > 1:  # First reset already done above
                    obs = env.reset()
                episode_reward = 0
                episode_wait_time = 0
                episode_speed_sum = 0
                speed_count = 0
                done = False
                step_count = 0
                max_steps = num_seconds // 5  # Max steps based on delta_time=5
                
                while not done and step_count < max_steps:
                    # Get actions from agents
                    actions = {ts_id: agents[ts_id].act(obs[ts_id]) for ts_id in obs.keys()}
                    
                    # Step environment (returns 4 values: obs, rewards, dones, info)
                    next_obs, rewards, dones, info = env.step(actions)
                    
                    # Debug: Print rewards for first few steps of first episode
                    if ep == 1 and step_count < 5:
                        print(f"  Step {step_count}: rewards = {rewards}")
                        if isinstance(rewards, dict):
                            for ts_id, r in rewards.items():
                                print(f"    {ts_id}: {r}")
                    
                    # Check if episode is done
                    done = all(dones.values()) if isinstance(dones, dict) else dones
                    step_count += 1
                    
                    # Update agents and accumulate rewards
                    step_reward = 0
                    for ts_id in next_obs.keys():
                        reward_value = rewards[ts_id] if isinstance(rewards, dict) else rewards
                        agents[ts_id].learn(
                            state=obs[ts_id],
                            action=actions[ts_id],
                            reward=reward_value,
                            next_state=next_obs[ts_id],
                            done=dones[ts_id] if isinstance(dones, dict) else dones,
                        )
                        episode_reward += reward_value
                        step_reward += reward_value
                    
                    # Extract metrics from info dict if available
                    if info and isinstance(info, dict):
                        # Try to get waiting time and speed from info
                        for ts_id, ts_info in info.items():
                            if isinstance(ts_info, dict):
                                if 'agents_total_waiting_time' in ts_info:
                                    episode_wait_time += ts_info['agents_total_waiting_time']
                                if 'system_mean_waiting_time' in ts_info:
                                    episode_wait_time += ts_info['system_mean_waiting_time']
                                if 'agents_mean_speed' in ts_info:
                                    episode_speed_sum += ts_info['agents_mean_speed']
                                    speed_count += 1
                                if 'system_mean_speed' in ts_info:
                                    episode_speed_sum += ts_info['system_mean_speed']
                                    speed_count += 1
                    
                    # Print step info every 50 steps
                    if step_count % 50 == 0:
                        print(f"  Episode {ep}, Step {step_count}: step_reward={step_reward:.2f}, cumulative={episode_reward:.2f}")
                    
                    obs = next_obs
                
                episode_rewards.append(episode_reward)
                
                # Store episode metrics
                avg_episode_wait = episode_wait_time / step_count if step_count > 0 else 0
                avg_episode_speed = episode_speed_sum / speed_count if speed_count > 0 else 0
                episode_wait_times.append(avg_episode_wait)
                episode_speeds.append(avg_episode_speed)
                
                print(f"Episode {ep}/{episodes} completed: {step_count} steps, total reward: {episode_reward:.2f}, avg_wait: {avg_episode_wait:.2f}, avg_speed: {avg_episode_speed:.2f}")
                
                # Update progress
                self.progress = int((ep / episodes) * 100)
                if callback:
                    callback(self.progress, ep, episodes)
            
            env.close()
            
            # Save trained agents
            agents_dir = f"trained_agents/{scenario}"
            os.makedirs(agents_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for ts_id, agent in agents.items():
                agent_file = f"{agents_dir}/{ts_id}_{timestamp}.pkl"
                agent.save(agent_file)
            
            print(f"\n✅ Trained agents saved to {agents_dir}/")
            
            print(f"\nTraining completed!")
            print(f"Episode rewards: {[f'{r:.2f}' for r in episode_rewards]}")
            print(f"Total reward sum: {sum(episode_rewards):.2f}")
            print(f"Average reward: {sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0:.2f}")
            print(f"Min reward: {min(episode_rewards) if episode_rewards else 0:.2f}")
            print(f"Max reward: {max(episode_rewards) if episode_rewards else 0:.2f}")
            
            # Load and analyze results
            results_file = f"{output_file}_conn0_ep{episodes}.csv"
            
            # Prepare agent files info
            agent_files = {ts_id: f"{agents_dir}/{ts_id}_{timestamp}.pkl" for ts_id in agents.keys()}
            
            # Try to find CSV file (sometimes naming is different)
            csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv') and 'simulation' in f]
            
            if csv_files:
                # Use the most recent CSV file
                csv_files.sort(reverse=True)
                results_file = os.path.join(output_dir, csv_files[0])
                print(f"\n📊 Loading results from: {results_file}")
            
            if os.path.exists(results_file):
                df = pd.read_csv(results_file)
                print(f"CSV loaded: {len(df)} rows")
                print(f"Available columns: {list(df.columns)}")
                
                # Calculate metrics from available columns
                metrics = {}
                
                # Check for system-level metrics
                if 'system_total_waiting_time' in df.columns:
                    metrics['avg_system_wait_time'] = float(df['system_total_waiting_time'].mean())
                    print(f"Average waiting time: {metrics['avg_system_wait_time']:.2f}s")
                elif episode_wait_times and any(w > 0 for w in episode_wait_times):
                    # Use our tracked metrics
                    metrics['avg_system_wait_time'] = sum(episode_wait_times) / len(episode_wait_times)
                    print(f"Average waiting time (from tracking): {metrics['avg_system_wait_time']:.2f}s")
                
                if 'system_mean_speed' in df.columns:
                    metrics['avg_system_speed'] = float(df['system_mean_speed'].mean())
                    print(f"Average speed: {metrics['avg_system_speed']:.2f} m/s")
                elif episode_speeds and any(s > 0 for s in episode_speeds):
                    # Use our tracked metrics
                    metrics['avg_system_speed'] = sum(episode_speeds) / len(episode_speeds)
                    print(f"Average speed (from tracking): {metrics['avg_system_speed']:.2f} m/s")
                
                if 'system_total_stopped' in df.columns:
                    metrics['total_stopped'] = int(df['system_total_stopped'].sum())
                    print(f"Total stopped vehicles: {metrics['total_stopped']}")
                
                # If system metrics not found, check for aggregated metrics
                if not metrics and 'agents_total_stopped' in df.columns:
                    print("Using agent-level metrics instead of system metrics")
                    metrics['total_stopped'] = int(df['agents_total_stopped'].sum()) if 'agents_total_stopped' in df.columns else 0
                
                # Calculate metrics
                self.results = {
                    'success': True,
                    'episodes': episodes,
                    'total_reward': sum(episode_rewards),
                    'avg_reward': sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0,
                    'final_reward': episode_rewards[-1] if episode_rewards else 0,
                    'episode_rewards': episode_rewards,
                    'metrics': metrics if metrics else {'note': 'Detailed metrics not available in CSV'},
                    'csv_file': results_file,
                    'agent_files': agent_files,
                    'scenario': scenario,
                    'parameters': {
                        'alpha': alpha,
                        'gamma': gamma,
                        'epsilon': epsilon,
                        'lambda': lamb,
                        'fourier_order': fourier_order
                    }
                }
            else:
                # If CSV not found, return basic results with tracked metrics
                print(f"⚠️ CSV file not found: {results_file}")
                
                metrics = {}
                if episode_wait_times and any(w > 0 for w in episode_wait_times):
                    metrics['avg_system_wait_time'] = sum(episode_wait_times) / len(episode_wait_times)
                    print(f"Using tracked waiting time: {metrics['avg_system_wait_time']:.2f}s")
                
                if episode_speeds and any(s > 0 for s in episode_speeds):
                    metrics['avg_system_speed'] = sum(episode_speeds) / len(episode_speeds)
                    print(f"Using tracked speed: {metrics['avg_system_speed']:.2f} m/s")
                
                self.results = {
                    'success': True,
                    'episodes': episodes,
                    'total_reward': sum(episode_rewards),
                    'avg_reward': sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0,
                    'final_reward': episode_rewards[-1] if episode_rewards else 0,
                    'episode_rewards': episode_rewards,
                    'metrics': metrics if metrics else {'note': 'Detailed metrics not available'},
                    'agent_files': agent_files,
                    'scenario': scenario,
                    'parameters': {
                        'alpha': alpha,
                        'gamma': gamma,
                        'epsilon': epsilon,
                        'lambda': lamb,
                        'fourier_order': fourier_order
                    }
                }
            
            self.is_running = False
            return self.results
            
        except Exception as e:
            self.is_running = False
            raise Exception(f"Simulation failed: {str(e)}")
    
    def run_async(self, callback=None, **kwargs):
        """Run simulation in background thread"""
        def _run():
            try:
                self.run_simulation(callback=callback, **kwargs)
            except Exception as e:
                self.results = {'success': False, 'error': str(e)}
                self.is_running = False
        
        thread = threading.Thread(target=_run)
        thread.start()
        return thread


# Singleton instance
simulation_manager = TrafficSimulation()
