"""
OpenStreetMap scenario definitions and management for UXsim
"""

import os
import sys
from datetime import datetime

try:
    from uxsim import World
    from uxsim.OSMImporter import OSMImporter
    UXSIM_AVAILABLE = True
except ImportError:
    UXSIM_AVAILABLE = False
    print("Warning: UXsim not installed. OSM features will not be available.")


class OSMScenarios:
    """Manage OpenStreetMap-based traffic simulation scenarios"""
    
    # Preset locations for quick access
    PRESETS = {
        'tokyo_highway': {
            'name': 'Tokyo Highway Network',
            'bounds': {
                'north': 35.817,
                'south': 35.570,
                'east': 139.881,
                'west': 139.583
            },
            'filter': '["highway"~"motorway"]',
            'description': 'Major highways in north Tokyo area',
            'country': 'Japan',
            'area_km2': 700,
            'recommended_vehicles': 5000
        },
        'mumbai_central': {
            'name': 'Mumbai Central Business District',
            'bounds': {
                'north': 19.00,
                'south': 18.90,
                'east': 72.85,
                'west': 72.80
            },
            'filter': '["highway"~"primary|secondary"]',
            'description': 'Main roads in Mumbai CBD',
            'country': 'India',
            'area_km2': 100,
            'recommended_vehicles': 3000
        },
        'london_central': {
            'name': 'Central London',
            'bounds': {
                'north': 51.55,
                'south': 51.45,
                'east': -0.05,
                'west': -0.20
            },
            'filter': '["highway"~"primary|secondary|tertiary"]',
            'description': 'Central London road network',
            'country': 'United Kingdom',
            'area_km2': 150,
            'recommended_vehicles': 4000
        },
        'nyc_manhattan': {
            'name': 'Manhattan, New York',
            'bounds': {
                'north': 40.80,
                'south': 40.70,
                'east': -73.90,
                'west': -74.00
            },
            'filter': '["highway"~"primary|secondary"]',
            'description': 'Manhattan street grid',
            'country': 'USA',
            'area_km2': 120,
            'recommended_vehicles': 5000
        },
        'delhi_connaught': {
            'name': 'Connaught Place, Delhi',
            'bounds': {
                'north': 28.65,
                'south': 28.60,
                'east': 77.23,
                'west': 77.18
            },
            'filter': '["highway"~"primary|secondary|tertiary"]',
            'description': 'Connaught Place and surrounding areas',
            'country': 'India',
            'area_km2': 80,
            'recommended_vehicles': 2500
        },
        'bangalore_mg_road': {
            'name': 'MG Road, Bangalore',
            'bounds': {
                'north': 12.98,
                'south': 12.93,
                'east': 77.63,
                'west': 77.58
            },
            'filter': '["highway"~"primary|secondary|tertiary"]',
            'description': 'MG Road commercial district',
            'country': 'India',
            'area_km2': 60,
            'recommended_vehicles': 2000
        }
    }
    
    @classmethod
    def get_available_presets(cls):
        """Get list of available preset locations"""
        return {
            key: {
                'name': val['name'],
                'description': val['description'],
                'country': val['country'],
                'area_km2': val['area_km2']
            }
            for key, val in cls.PRESETS.items()
        }
    
    @classmethod
    def run_osm_simulation(cls, scenario_key=None, custom_bounds=None, 
                          custom_filter=None, duration=7200, 
                          demand_volume=5000, output_dir='outputs'):
        """
        Run OpenStreetMap-based traffic simulation
        
        Args:
            scenario_key: Key for preset scenario (e.g., 'tokyo_highway')
            custom_bounds: Dict with north, south, east, west (overrides preset)
            custom_filter: OSM filter string (overrides preset)
            duration: Simulation duration in seconds
            demand_volume: Number of vehicles to generate
            output_dir: Directory to save outputs
            
        Returns:
            dict: Simulation results and file paths
        """
        if not UXSIM_AVAILABLE:
            raise Exception("UXsim is not installed. Please install it to use OSM features.")
        
        # Get scenario configuration
        if scenario_key and scenario_key in cls.PRESETS:
            config = cls.PRESETS[scenario_key]
            bounds = config['bounds']
            osm_filter = config['filter']
            scenario_name = config['name']
        elif custom_bounds:
            bounds = custom_bounds
            osm_filter = custom_filter or '["highway"~"primary|secondary"]'
            scenario_name = "Custom Location"
        else:
            raise ValueError("Must provide either scenario_key or custom_bounds")
        
        # Create World
        W = World(
            name=f"osm_{scenario_key or 'custom'}",
            deltan=5,
            tmax=duration,
            print_mode=1,
            save_mode=1,
            show_mode=0,
            random_seed=0
        )
        
        print(f"📍 Loading {scenario_name} from OpenStreetMap...")
        print(f"   Filter: {osm_filter}")
        print(f"   Bounds: N={bounds['north']:.4f}, S={bounds['south']:.4f}, E={bounds['east']:.4f}, W={bounds['west']:.4f}")
        
        # Import OSM data
        try:
            nodes, links = OSMImporter.import_osm_data(
                north=bounds['north'],
                south=bounds['south'],
                east=bounds['east'],
                west=bounds['west'],
                custom_filter=osm_filter
            )
            
            print(f"   Raw import: {len(nodes)} nodes and {len(links)} links")
            
            # If no data found, try with more inclusive filter
            if len(links) == 0:
                print("   ⚠️ No roads found with initial filter, trying broader filter...")
                fallback_filter = '["highway"~"motorway|trunk|primary|secondary|tertiary"]'
                nodes, links = OSMImporter.import_osm_data(
                    north=bounds['north'],
                    south=bounds['south'],
                    east=bounds['east'],
                    west=bounds['west'],
                    custom_filter=fallback_filter
                )
                print(f"   Fallback import: {len(nodes)} nodes and {len(links)} links")
            
            if len(links) == 0:
                raise Exception("No road network found in this area. The selected area might be too small or have no suitable roads. Try selecting a larger urban area.")
            
            print(f"✅ Imported {len(nodes)} nodes and {len(links)} links")
            
            # Post-process network
            nodes, links = OSMImporter.osm_network_postprocessing(
                nodes, links,
                node_merge_threshold=0.01,  # ~1km merge distance (increased from 500m)
                node_merge_iteration=3,  # Reduced iterations
                enforce_bidirectional=True
            )
            
            print(f"✅ After processing: {len(nodes)} nodes and {len(links)} links")
            
        except Exception as e:
            raise Exception(f"Failed to import OSM data: {str(e)}")
        
        # Validate network has content
        if len(nodes) == 0 or len(links) == 0:
            raise Exception(f"No road network found in this area with filter {osm_filter}. Try a larger area or different road filter.")
        
        # Convert to UXsim World
        print(f"🔧 Converting OSM network to UXsim World...")
        OSMImporter.osm_network_to_World(
            W, nodes, links,
            default_jam_density=0.2,
            coef_degree_to_meter=111000
        )
        
        # Verify World has nodes and links
        if len(W.NODES) == 0 or len(W.LINKS) == 0:
            raise Exception("Failed to convert OSM network to UXsim World. Network is empty.")
        
        print(f"✅ World created with {len(W.NODES)} nodes and {len(W.LINKS)} links")
        
        # Add demand - create traffic between random node pairs
        print(f"🚗 Adding {demand_volume} vehicles/hour of demand...")
        
        # Get all nodes as potential origins/destinations
        # W.NODES is a list, not a dict
        all_nodes = W.NODES
        
        if len(all_nodes) < 2:
            raise Exception("Not enough nodes in network to create demand")
        
        # Create demand between random node pairs
        import random
        random.seed(0)
        
        # Sample 20% of nodes as origins and destinations
        num_od_pairs = max(10, len(all_nodes) // 5)
        
        for i in range(num_od_pairs):
            # Pick random origin and destination
            origin = random.choice(all_nodes)
            destination = random.choice(all_nodes)
            
            # Skip if same node
            if origin == destination:
                continue
            
            # Add demand
            W.adddemand(
                origin, destination,
                0, 3600,  # First hour
                volume=demand_volume // num_od_pairs
            )
        
        # Run simulation
        print(f"🔄 Starting simulation ({duration}s)...")
        W.exec_simulation()
        
        # Analyze results
        print("📊 Analyzing results...")
        W.analyzer.print_simple_stats()
        
        # Generate outputs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f"osm_{scenario_key or 'custom'}_{timestamp}")
        os.makedirs(output_path, exist_ok=True)
        
        # Create visualizations
        print("📸 Creating visualizations...")
        
        try:
            # Save current directory and change to output directory
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            # Network snapshots at different times
            for t in range(0, W.TMAX, int(W.TMAX / 6)):
                try:
                    W.analyzer.network(t, detailed=0, network_font_size=0, figsize=(12, 12))
                    # Manually save the figure
                    import matplotlib.pyplot as plt
                    plt.savefig(f"{output_path}/network_t{t}.png", dpi=150, bbox_inches='tight')
                    plt.close()
                except Exception as e:
                    print(f"⚠️ Warning: Could not create snapshot at t={t}: {e}")
            
            # Save animation
            try:
                W.analyzer.network_anim(animation_speed_inverse=15, detailed=0, network_font_size=0)
                # The animation is saved to W.name directory, move it
                import shutil
                src = f"out{W.name}/anim_network.gif"
                if os.path.exists(src):
                    shutil.copy(src, f"{output_path}/network_animation.gif")
            except Exception as e:
                print(f"⚠️ Warning: Could not create network animation: {e}")
            
            # Fancy animation with vehicle traces
            try:
                W.analyzer.network_fancy(animation_speed_inverse=15, sample_ratio=0.3, interval=10, trace_length=5)
                # The animation is saved to W.name directory, move it
                src = f"out{W.name}/anim_network_fancy.gif"
                if os.path.exists(src):
                    shutil.copy(src, f"{output_path}/network_fancy.gif")
            except Exception as e:
                print(f"⚠️ Warning: Could not create fancy animation: {e}")
                
        except Exception as e:
            print(f"⚠️ Warning: Visualization generation had issues: {e}")
        
        # Output data
        W.analyzer.output_data()
        
        # Collect statistics - convert NumPy types to Python native types for JSON serialization
        stats = {
            'scenario_name': scenario_name,
            'nodes': int(len(nodes)),
            'links': int(len(links)),
            'duration': int(duration),
            'demand_volume': int(demand_volume),
            'total_trips': int(W.analyzer.trip_all) if hasattr(W.analyzer, 'trip_all') else 0,
            'average_speed': float(W.analyzer.average_speed) if hasattr(W.analyzer, 'average_speed') else 0.0,
            'output_path': output_path,
            'animations': {
                'network': f"osm_{scenario_key or 'custom'}_{timestamp}/network_animation.gif",
                'fancy': f"osm_{scenario_key or 'custom'}_{timestamp}/network_fancy.gif"
            },
            'snapshots': [f"osm_{scenario_key or 'custom'}_{timestamp}/network_t{t}.png" for t in range(0, W.TMAX, int(W.TMAX / 6))]
        }
        
        print(f"✅ Simulation complete! Results saved to {output_path}")
        
        return stats
    
    @classmethod
    def validate_bounds(cls, north, south, east, west):
        """Validate coordinate bounds"""
        if not (-90 <= south < north <= 90):
            return False, "Invalid latitude values"
        if not (-180 <= west < east <= 180):
            return False, "Invalid longitude values"
        
        # Check area size (warn if too large)
        lat_diff = north - south
        lon_diff = east - west
        area_approx = lat_diff * lon_diff * 111 * 111  # Rough km²
        
        if area_approx > 1000:
            return False, f"Area too large (~{area_approx:.0f} km²). Please select smaller area (<1000 km²)"
        
        return True, "Valid"


# Singleton instance
osm_scenarios = OSMScenarios()
