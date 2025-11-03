"""
Custom SUMO network loader and generator
Allows users to upload custom .net.xml files or use pre-built scenarios
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)

try:
    from sumo_rl import SumoEnvironment
    import sumolib
    SUMO_AVAILABLE = True
except ImportError:
    SUMO_AVAILABLE = False


class NetworkManager:
    """Manage SUMO network files and scenarios"""
    
    AVAILABLE_SCENARIOS = {
        'cologne8': {
            'name': 'Cologne 8-Way Intersection',
            'description': 'Complex 8-way intersection in Cologne, Germany',
            'difficulty': 'Hard',
            'built_in': True
        },
        'cologne1': {
            'name': 'Cologne 1-Way Intersection',
            'description': 'Simple single intersection',
            'difficulty': 'Easy',
            'built_in': True
        },
        'cologne3': {
            'name': 'Cologne 3-Way Network',
            'description': 'Network with 3 intersections',
            'difficulty': 'Medium',
            'built_in': True
        },
        'arterial4x4': {
            'name': '4x4 Arterial Grid',
            'description': 'Grid network with 16 intersections',
            'difficulty': 'Very Hard',
            'built_in': True
        },
        'ingolstadt1': {
            'name': 'Ingolstadt 1',
            'description': 'Real-world intersection from Ingolstadt',
            'difficulty': 'Medium',
            'built_in': True
        },
    }
    
    def __init__(self):
        self.networks_dir = Path("networks")
        self.networks_dir.mkdir(exist_ok=True)
        self.custom_networks_dir = self.networks_dir / "custom"
        self.custom_networks_dir.mkdir(exist_ok=True)
    
    def get_available_scenarios(self):
        """Get list of all available scenarios (built-in + custom)"""
        scenarios = dict(self.AVAILABLE_SCENARIOS)
        
        # Add custom uploaded networks
        for net_file in self.custom_networks_dir.glob("*.net.xml"):
            net_id = net_file.stem
            scenarios[net_id] = {
                'name': net_id.replace('_', ' ').title(),
                'description': 'Custom uploaded network',
                'difficulty': 'Unknown',
                'built_in': False,
                'path': str(net_file)
            }
        
        return scenarios
    
    def create_environment(self, scenario_id, **kwargs):
        """Create SUMO environment for given scenario"""
        if not SUMO_AVAILABLE:
            raise Exception("SUMO-RL not available")
        
        from sumo_rl import SumoEnvironment
        
        # Check if it's a built-in scenario
        if scenario_id in ['cologne8', 'cologne1', 'cologne3', 'arterial4x4', 'ingolstadt1']:
            # Get the path to sumo_rl package
            import sumo_rl
            sumo_rl_path = os.path.join(os.path.dirname(sumo_rl.__file__), 'nets')
            
            # Map scenario to net directories
            scenario_dirs = {
                'cologne8': os.path.join(sumo_rl_path, 'RESCO', 'cologne8'),
                'cologne1': os.path.join(sumo_rl_path, 'RESCO', 'cologne1'),
                'cologne3': os.path.join(sumo_rl_path, 'RESCO', 'cologne3'),
                'arterial4x4': os.path.join(sumo_rl_path, 'RESCO', 'arterial4x4'),
                'ingolstadt1': os.path.join(sumo_rl_path, 'RESCO', 'ingolstadt1'),
            }
            
            net_dir = scenario_dirs.get(scenario_id)
            
            if not net_dir or not os.path.exists(net_dir):
                raise Exception(f"Scenario directory not found: {scenario_id}")
            
            # Find the .net.xml and .rou.xml files
            net_file = None
            route_file = None
            
            for f in os.listdir(net_dir):
                if f.endswith('.net.xml'):
                    net_file = os.path.join(net_dir, f)
                elif f.endswith('.rou.xml'):
                    route_file = os.path.join(net_dir, f)
            
            if not net_file or not route_file:
                raise Exception(f"Network files not found in {net_dir}")
            
            print(f"Using network: {net_file}")
            print(f"Using routes: {route_file}")
            
            return SumoEnvironment(
                net_file=net_file,
                route_file=route_file,
                **kwargs
            )
        else:
            # Custom network
            scenarios = self.get_available_scenarios()
            if scenario_id not in scenarios:
                raise ValueError(f"Unknown scenario: {scenario_id}")
            
            net_path = scenarios[scenario_id]['path']
            route_path = net_path.replace('.net.xml', '.rou.xml')
            
            # Create environment with custom network
            env = SumoEnvironment(
                net_file=net_path,
                route_file=route_path,
                **kwargs
            )
            return env
    
    def save_custom_network(self, net_xml_content, route_xml_content, network_name):
        """Save custom SUMO network files"""
        network_name = network_name.replace(' ', '_').lower()
        
        net_path = self.custom_networks_dir / f"{network_name}.net.xml"
        route_path = self.custom_networks_dir / f"{network_name}.rou.xml"
        
        with open(net_path, 'w') as f:
            f.write(net_xml_content)
        
        with open(route_path, 'w') as f:
            f.write(route_xml_content)
        
        return network_name
    
    def validate_network(self, net_xml_path):
        """Validate SUMO network file"""
        try:
            tree = ET.parse(net_xml_path)
            root = tree.getroot()
            
            # Check if it's a valid SUMO network
            if root.tag != 'net':
                return False, "Not a valid SUMO network file"
            
            # Count junctions
            junctions = root.findall('.//junction[@type="traffic_light"]')
            if not junctions:
                return False, "No traffic light junctions found"
            
            return True, f"Valid network with {len(junctions)} traffic lights"
        except Exception as e:
            return False, str(e)
    
    def generate_simple_grid(self, rows=2, cols=2, name="custom_grid"):
        """Generate a simple grid network using netgenerate"""
        if not SUMO_AVAILABLE:
            raise Exception("SUMO not available")
        
        network_name = f"{name}_{rows}x{cols}"
        net_path = self.custom_networks_dir / f"{network_name}.net.xml"
        
        # Use SUMO's netgenerate to create grid
        import subprocess
        
        netgenerate_path = os.path.join(os.environ.get('SUMO_HOME', ''), 'bin', 'netgenerate')
        if os.name == 'nt':  # Windows
            netgenerate_path += '.exe'
        
        cmd = [
            netgenerate_path,
            '--grid',
            '--grid.number', f'{cols}',
            '--grid.length', '200',
            '--grid.attach-length', '100',
            '--output-file', str(net_path),
            '--tls.guess', 'true'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Generate simple route file
            self._generate_simple_routes(net_path, network_name)
            
            return network_name
        except Exception as e:
            raise Exception(f"Failed to generate network: {str(e)}")
    
    def _generate_simple_routes(self, net_path, network_name):
        """Generate simple route file for the network"""
        route_path = self.custom_networks_dir / f"{network_name}.rou.xml"
        
        # Simple route template
        route_content = """<?xml version="1.0" encoding="UTF-8"?>
<routes>
    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5" maxSpeed="50"/>
    
    <flow id="flow_0" type="car" begin="0" end="3600" probability="0.1" from="gneE0" to="gneE1"/>
    <flow id="flow_1" type="car" begin="0" end="3600" probability="0.1" from="gneE1" to="gneE0"/>
</routes>"""
        
        with open(route_path, 'w') as f:
            f.write(route_content)


# Global instance
network_manager = NetworkManager()
