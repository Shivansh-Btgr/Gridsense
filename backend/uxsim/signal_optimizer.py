"""
Signal timing optimization for real-world OSM networks
"""

import os
from datetime import datetime

try:
    from uxsim import World
    from uxsim.OSMImporter import OSMImporter
    from uxsim.TaxiHandler import TaxiHandler_nearest
    UXSIM_AVAILABLE = True
except ImportError:
    UXSIM_AVAILABLE = False


class SignalOptimizer:
    """Optimize signal timings for OSM-based networks"""
    
    def __init__(self):
        self.W = None
        self.nodes = []
        self.links = []
        self.signal_nodes = []
    
    def load_network_from_osm(self, north, south, east, west, osm_filter='["highway"~"primary|secondary"]'):
        """Load network from OpenStreetMap"""
        if not UXSIM_AVAILABLE:
            raise Exception("UXsim not installed")
        
        # Import OSM data
        nodes, links = OSMImporter.import_osm_data(
            north=north,
            south=south,
            east=east,
            west=west,
            custom_filter=osm_filter
        )
        
        if len(links) == 0:
            # Try broader filter
            fallback_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary"]'
            nodes, links = OSMImporter.import_osm_data(
                north=north, south=south, east=east, west=west,
                custom_filter=fallback_filter
            )
        
        if len(links) == 0:
            raise Exception("No road network found in this area")
        
        print(f"📥 Raw OSM import: {len(nodes)} nodes, {len(links)} links")
        
        # Post-process network - use less aggressive merging to preserve intersections
        nodes, links = OSMImporter.osm_network_postprocessing(
            nodes, links,
            node_merge_threshold=0.005,  # 500m merge distance (less aggressive)
            node_merge_iteration=2,  # Fewer iterations
            enforce_bidirectional=True
        )
        
        print(f"📥 After post-processing: {len(nodes)} nodes, {len(links)} links")
        
        # Validate we have enough nodes
        if len(nodes) < 3:
            raise Exception(f"Network too small after processing ({len(nodes)} nodes). Please select a larger area with more roads.")
        
        self.nodes = nodes
        self.links = links
        
        # Find potential signal nodes (intersections with 3+ connections)
        self.signal_nodes = self._find_signal_nodes()
        
        return {
            'nodes': len(nodes),
            'links': len(links),
            'signal_candidates': len(self.signal_nodes)
        }
    
    def _find_signal_nodes(self):
        """Find nodes that are good candidates for traffic signals"""
        node_connections = {}
        
        # Count connections for each node
        # OSM links format: [start_node, end_node, length, ...]
        for link in self.links:
            if isinstance(link, list) or isinstance(link, tuple):
                start_node = link[0]
                end_node = link[1]
            else:
                # Fallback for dict format
                start_node = link.get('start_node')
                end_node = link.get('end_node')
            
            node_connections[start_node] = node_connections.get(start_node, 0) + 1
            node_connections[end_node] = node_connections.get(end_node, 0) + 1
        
        print(f"📊 Node connection counts: {node_connections}")
        print(f"📍 Total nodes in network: {len(self.nodes)}")
        
        # Find nodes with 2+ connections (lowered threshold for small networks)
        # For signal tuning, even 2-way intersections can be useful
        signal_candidates = []
        
        for node_id, connections in node_connections.items():
            # Skip empty or invalid node IDs
            if node_id == '' or node_id is None:
                continue
            
            # Use 2+ connections instead of 3+ for small networks
            if connections >= 2:
                # Find this node in our nodes list by ID
                node_index = None
                for idx, node in enumerate(self.nodes):
                    # OSM nodes format: [x, y, ...]
                    # The node ID might be stored differently, so we'll use index
                    # For now, assume nodes are in order
                    if idx == node_id or (isinstance(node_id, int) and idx == node_id):
                        node_index = idx
                        break
                
                if node_index is None:
                    # If we can't find by ID, just use all nodes
                    if isinstance(node_id, int) and 0 <= node_id < len(self.nodes):
                        node_index = node_id
                    else:
                        continue
                
                node = self.nodes[node_index]
                
                # OSM nodes format: [x, y, ...]
                if isinstance(node, list) or isinstance(node, tuple):
                    x, y = node[0], node[1]
                else:
                    x, y = node.get('x'), node.get('y')
                
                print(f"✅ Found signal candidate: Node {node_id} (index {node_index}) with {connections} connections")
                    
                signal_candidates.append({
                    'id': node_index,  # Use index for later reference
                    'x': float(x),
                    'y': float(y),
                    'connections': connections
                })
        
        # If still no candidates, just add all nodes
        if len(signal_candidates) == 0:
            print("⚠️ No multi-connection nodes found. Adding all nodes as candidates.")
            for idx, node in enumerate(self.nodes):
                if isinstance(node, list) or isinstance(node, tuple):
                    x, y = node[0], node[1]
                else:
                    x, y = node.get('x', 0), node.get('y', 0)
                
                signal_candidates.append({
                    'id': idx,
                    'x': float(x),
                    'y': float(y),
                    'connections': node_connections.get(idx, 0)
                })
        
        print(f"🚦 Total signal candidates found: {len(signal_candidates)}")
        return signal_candidates
    
    def create_world_with_signals(self, signal_settings, duration=3600, demand_volume=2000):
        """Create UXsim World with customized signal timings"""
        if not self.nodes or not self.links:
            raise Exception("Network not loaded. Call load_network_from_osm first.")
        
        # Create World
        self.W = World(
            name="signal_optimization",
            deltan=5,
            tmax=duration,
            print_mode=1,
            save_mode=1,
            show_mode=0,
            random_seed=0
        )
        
        # Convert OSM network to World
        OSMImporter.osm_network_to_World(
            self.W, self.nodes, self.links,
            default_jam_density=0.2,
            coef_degree_to_meter=111000
        )
        
        # Apply signal settings to selected nodes
        for setting in signal_settings:
            node_id = setting['node_id']
            
            if node_id < len(self.W.NODES):
                node = self.W.NODES[node_id]
                
                # Set signal parameters
                cycle = setting.get('cycle', 120)  # Total cycle time
                green_time = setting.get('green_time', 60)  # Green time
                offset = setting.get('offset', 0)  # Offset from cycle start
                
                # Create signal pattern [green, red]
                red_time = cycle - green_time
                node.signal = [green_time, red_time]
                node.signal_offset = offset
                node.signal_phase = 0
        
        # Add random demand
        import random
        random.seed(0)
        
        all_nodes = self.W.NODES
        num_od_pairs = max(10, len(all_nodes) // 5)
        
        for i in range(num_od_pairs):
            origin = random.choice(all_nodes)
            destination = random.choice(all_nodes)
            
            if origin != destination:
                self.W.adddemand(
                    origin, destination,
                    0, duration,
                    volume=demand_volume // num_od_pairs
                )
        
        return {
            'world_created': True,
            'nodes': len(self.W.NODES),
            'links': len(self.W.LINKS)
        }
    
    def run_simulation(self, output_dir):
        """Run simulation and return results"""
        if not self.W:
            raise Exception("World not created. Call create_world_with_signals first.")
        
        # Run simulation
        self.W.exec_simulation()
        
        # Analyze results
        self.W.analyzer.print_simple_stats()
        
        # Generate outputs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f"signal_opt_{timestamp}")
        os.makedirs(output_path, exist_ok=True)
        
        # Create visualizations
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import shutil
            
            print("📸 Creating visualizations...")
            
            # Time-space diagram - UXsim saves to its own output directory
            print("   Creating time-space diagram...")
            uxsim_output_dir = f"out{self.W.name}"
            
            if len(self.W.LINKS) > 0:
                try:
                    # Get first few links for diagram
                    main_link_names = [link.name for link in self.W.LINKS[:min(5, len(self.W.LINKS))] if hasattr(link, 'name')]
                    
                    if main_link_names:
                        print(f"      Plotting links: {main_link_names}")
                        # This will save to uxsim_output_dir automatically
                        self.W.analyzer.time_space_diagram_traj_links(main_link_names)
                        
                        # Find and copy the generated file
                        if os.path.exists(uxsim_output_dir):
                            for filename in os.listdir(uxsim_output_dir):
                                if filename.startswith('tsd_traj_links') and filename.endswith('.png'):
                                    src = os.path.join(uxsim_output_dir, filename)
                                    dst = f"{output_path}/time_space_diagram.png"
                                    shutil.copy(src, dst)
                                    print(f"      ✅ Copied {filename}")
                                    break
                except Exception as e:
                    print(f"      ⚠️ Time-space diagram error: {e}")
            
            # Network snapshot at final time with labeled axes
            print("   Creating network snapshot...")
            fig, ax = plt.subplots(figsize=(14, 14))
            self.W.analyzer.network(self.W.TMAX, detailed=0, network_font_size=0, figsize=(14, 14))
            
            # Add axis labels
            ax = plt.gca()
            ax.set_xlabel('Longitude (degrees)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Latitude (degrees)', fontsize=12, fontweight='bold')
            ax.set_title(f'Network State at t={self.W.TMAX}s\n(Node colors indicate traffic load, Link thickness shows capacity)', 
                        fontsize=14, fontweight='bold', pad=20)
            
            plt.savefig(f"{output_path}/network_final.png", dpi=150, bbox_inches='tight')
            plt.close()
            print("      ✅ Network snapshot saved")
            
            print("✅ All visualizations completed")
                
        except Exception as e:
            print(f"⚠️ Warning: Visualization error: {e}")
            import traceback
            traceback.print_exc()
        
        # Collect statistics
        # Only include specific visualizations in order
        viz_files = {}
        
        # 1. Time-space diagram (if exists)
        time_space_path = f"{output_path}/time_space_diagram.png"
        if os.path.exists(time_space_path):
            viz_files['Time-Space Diagram'] = f"signal_opt_{timestamp}/time_space_diagram.png"
        
        # 2. Network final state
        network_path = f"{output_path}/network_final.png"
        if os.path.exists(network_path):
            viz_files['Network Final State'] = f"signal_opt_{timestamp}/network_final.png"
        
        stats = {
            'total_trips': int(self.W.analyzer.trip_all) if hasattr(self.W.analyzer, 'trip_all') else 0,
            'average_speed': float(self.W.analyzer.average_speed) if hasattr(self.W.analyzer, 'average_speed') else 0.0,
            'total_travel_time': float(self.W.analyzer.total_travel_time) if hasattr(self.W.analyzer, 'total_travel_time') else 0.0,
            'average_travel_time': 0.0,
            'output_path': f"signal_opt_{timestamp}",
            'visualizations': viz_files
        }
        
        # Calculate average travel time
        if stats['total_trips'] > 0:
            stats['average_travel_time'] = stats['total_travel_time'] / stats['total_trips']
        
        return stats
    
    def run_mode_comparison(self, signal_settings, duration=3600, demand_volume=2000, 
                           rideshare_percent=50, num_taxis=100, output_dir="outputs"):
        """Run comparison between private cars only vs rideshare modes"""
        if not self.nodes or not self.links:
            raise Exception("Network not loaded. Call load_network_from_osm first.")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Calculate splits
        n_rideshare_travelers = int(demand_volume * rideshare_percent / 100)
        n_car_travelers = demand_volume - n_rideshare_travelers
        
        print(f"\n{'='*60}")
        print(f"🚗 MODE COMPARISON SIMULATION")
        print(f"{'='*60}")
        print(f"Total Demand: {demand_volume} trips")
        print(f"Private Cars: {n_car_travelers} ({100-rideshare_percent}%)")
        print(f"Rideshare Users: {n_rideshare_travelers} ({rideshare_percent}%)")
        print(f"Available Taxis: {num_taxis}")
        print(f"{'='*60}\n")
        
        results = {}
        
        # Scenario 1: All Private Cars
        print("🚙 Scenario 1: ALL PRIVATE CARS")
        results['private_only'] = self._run_single_mode_scenario(
            signal_settings, duration, demand_volume, 
            rideshare_percent=0, num_taxis=0,
            scenario_name="private_only", timestamp=timestamp, output_dir=output_dir
        )
        
        # Scenario 2: Mixed Mode (if rideshare > 0)
        if rideshare_percent > 0:
            print(f"\n🚕 Scenario 2: MIXED MODE ({rideshare_percent}% Rideshare)")
            results['mixed'] = self._run_single_mode_scenario(
                signal_settings, duration, demand_volume,
                rideshare_percent=rideshare_percent, num_taxis=num_taxis,
                scenario_name="mixed", timestamp=timestamp, output_dir=output_dir
            )
        
        # Compare results
        comparison = self._compare_scenarios(results)
        
        return {
            'scenarios': results,
            'comparison': comparison,
            'timestamp': timestamp
        }
    
    def _run_single_mode_scenario(self, signal_settings, duration, demand_volume,
                                  rideshare_percent, num_taxis, scenario_name, timestamp, output_dir):
        """Run a single transportation mode scenario"""
        import random
        random.seed(0)
        
        # Create World
        W = World(
            name=f"mode_{scenario_name}",
            deltan=5,
            tmax=duration,
            print_mode=1,
            save_mode=1,
            show_mode=0,
            random_seed=0
        )
        
        # Convert OSM network to World
        OSMImporter.osm_network_to_World(
            W, self.nodes, self.links,
            default_jam_density=0.2,
            coef_degree_to_meter=111000
        )
        
        # Apply signal settings
        for setting in signal_settings:
            node_id = setting['node_id']
            if node_id < len(W.NODES):
                node = W.NODES[node_id]
                cycle = setting.get('cycle', 120)
                green_time = setting.get('green_time', 60)
                offset = setting.get('offset', 0)
                red_time = cycle - green_time
                node.signal = [green_time, red_time]
                node.signal_offset = offset
                node.signal_phase = 0
        
        # Calculate demand splits
        n_rideshare_travelers = int(demand_volume * rideshare_percent / 100)
        n_car_travelers = demand_volume - n_rideshare_travelers
        
        all_nodes = W.NODES
        num_od_pairs = max(10, len(all_nodes) // 5)
        
        # Setup rideshare handler if needed
        taxi_handler = None
        if rideshare_percent > 0 and num_taxis > 0:
            taxi_handler = TaxiHandler_nearest(W)
            
            # Add taxis
            for i in range(num_taxis):
                node = random.choice(all_nodes)
                W.addVehicle(node, None, 0, mode="taxi")
            
            # Add rideshare travelers
            for i in range(n_rideshare_travelers):
                origin = random.choice(all_nodes)
                destination = random.choice(all_nodes)
                if origin != destination:
                    request_time = random.uniform(0, duration * 0.5)
                    taxi_handler.add_trip_request(origin, destination, request_time)
        
        # Add private car travelers
        for i in range(n_car_travelers):
            origin = random.choice(all_nodes)
            destination = random.choice(all_nodes)
            if origin != destination:
                depart_time = random.uniform(0, duration * 0.5)
                W.addVehicle(origin, destination, depart_time)
        
        print(f"   Added {n_car_travelers} private cars, {n_rideshare_travelers} rideshare trips, {num_taxis} taxis")
        
        # Run simulation with taxi assignment
        print(f"   Running simulation...")
        if taxi_handler:
            step_duration = 60  # Assign taxis every 60 seconds
            for t in range(0, duration, step_duration):
                W.exec_simulation(duration_t=step_duration)
                taxi_handler.assign_trip_request_to_taxi()
        else:
            W.exec_simulation()
        
        # Analyze results
        W.analyzer.print_simple_stats()
        
        # Get taxi stats
        taxi_stats = {}
        if taxi_handler:
            taxi_handler.print_stats()
            # Extract taxi statistics
            taxi_stats = {
                'waiting_time': float(taxi_handler.average_waiting_time) if hasattr(taxi_handler, 'average_waiting_time') else 0.0,
                'in_vehicle_time': float(taxi_handler.average_in_vehicle_time) if hasattr(taxi_handler, 'average_in_vehicle_time') else 0.0,
                'total_trips': int(taxi_handler.n_trip) if hasattr(taxi_handler, 'n_trip') else 0,
                'utilization': float(taxi_handler.average_utilization) if hasattr(taxi_handler, 'average_utilization') else 0.0
            }
        
        # Save network visualization
        output_path = os.path.join(output_dir, f"mode_comp_{timestamp}_{scenario_name}")
        os.makedirs(output_path, exist_ok=True)
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(12, 12))
            W.analyzer.network(W.TMAX, detailed=0, network_font_size=0, figsize=(12, 12))
            ax = plt.gca()
            ax.set_xlabel('Longitude (degrees)', fontsize=10)
            ax.set_ylabel('Latitude (degrees)', fontsize=10)
            mode_name = "All Private Cars" if rideshare_percent == 0 else f"Mixed ({rideshare_percent}% Rideshare)"
            ax.set_title(f'{mode_name}\nFinal Network State', fontsize=12, fontweight='bold')
            plt.savefig(f"{output_path}/network.png", dpi=120, bbox_inches='tight')
            plt.close()
        except Exception as e:
            print(f"   ⚠️ Visualization error: {e}")
        
        # Return statistics
        stats = {
            'scenario': scenario_name,
            'mode_name': "All Private Cars" if rideshare_percent == 0 else f"Mixed ({rideshare_percent}% Rideshare)",
            'total_trips': int(W.analyzer.trip_all) if hasattr(W.analyzer, 'trip_all') else 0,
            'average_speed': float(W.analyzer.average_speed) if hasattr(W.analyzer, 'average_speed') else 0.0,
            'total_travel_time': float(W.analyzer.total_travel_time) if hasattr(W.analyzer, 'total_travel_time') else 0.0,
            'average_travel_time': 0.0,
            'total_vehicles': n_car_travelers + num_taxis,
            'private_cars': n_car_travelers,
            'rideshare_trips': n_rideshare_travelers,
            'num_taxis': num_taxis,
            'taxi_stats': taxi_stats,
            'visualization': f"mode_comp_{timestamp}_{scenario_name}/network.png"
        }
        
        if stats['total_trips'] > 0:
            stats['average_travel_time'] = stats['total_travel_time'] / stats['total_trips']
        
        print(f"   ✅ Scenario complete: {stats['total_trips']} trips, {stats['average_speed']:.2f} m/s avg speed\n")
        
        return stats
    
    def _compare_scenarios(self, results):
        """Compare different mode scenarios"""
        comparison = {
            'winner': None,
            'metrics': {}
        }
        
        if 'private_only' in results and 'mixed' in results:
            private = results['private_only']
            mixed = results['mixed']
            
            # Compare key metrics
            comparison['metrics'] = {
                'speed_improvement': ((mixed['average_speed'] - private['average_speed']) / private['average_speed'] * 100) if private['average_speed'] > 0 else 0,
                'time_reduction': ((private['average_travel_time'] - mixed['average_travel_time']) / private['average_travel_time'] * 100) if private['average_travel_time'] > 0 else 0,
                'vehicle_reduction': ((private['total_vehicles'] - mixed['total_vehicles']) / private['total_vehicles'] * 100) if private['total_vehicles'] > 0 else 0
            }
            
            # Determine winner (lower travel time is better)
            if mixed['average_travel_time'] < private['average_travel_time']:
                comparison['winner'] = 'mixed'
            else:
                comparison['winner'] = 'private_only'
        
        return comparison


# Singleton instance
signal_optimizer = SignalOptimizer()
