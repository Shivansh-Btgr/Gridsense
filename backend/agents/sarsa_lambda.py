"""
True Online SARSA(λ) with Linear Function Approximation

This is a placeholder implementation. If you have the original linear_rl package,
you can replace this file with the actual implementation.
"""

import numpy as np


class TrueOnlineSarsaLambda:
    """True Online SARSA(λ) with Fourier basis function approximation"""
    
    def __init__(self, observation_space, action_space, alpha=0.01, gamma=0.95, 
                 epsilon=0.1, lamb=0.9, fourier_order=3):
        """
        Initialize SARSA agent
        
        Args:
            observation_space: Gym observation space
            action_space: Gym action space  
            alpha: Learning rate
            gamma: Discount factor
            epsilon: Exploration rate
            lamb: Lambda for eligibility traces
            fourier_order: Order of Fourier basis (keep low, e.g., 2-4)
        """
        self.observation_space = observation_space
        self.action_space = action_space
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.lamb = lamb
        
        # Limit Fourier order to prevent memory issues
        self.fourier_order = min(fourier_order, 5)  # Max order 5
        
        # Get dimensions
        try:
            self.state_dim = observation_space.shape[0]
        except:
            self.state_dim = 1
            
        try:
            self.n_actions = action_space.n
        except:
            self.n_actions = 2
        
        # Store original state dimension for proper feature computation
        self.original_state_dim = self.state_dim
        
        # Use reduced dimension for Fourier basis to prevent memory issues
        # but keep original for actual state processing
        self.fourier_state_dim = min(self.state_dim, 6)  # Use max 6 dims for Fourier
        
        # Calculate number of features (will be limited in generation)
        self.n_features = (self.fourier_order + 1) ** self.fourier_state_dim
        
        # Initialize weights and eligibility traces (will be resized in generation)
        self.weights = np.zeros((self.n_actions, 100))  # Temporary
        self.traces = np.zeros((self.n_actions, 100))   # Temporary
        
        # Generate Fourier coefficients
        self._generate_fourier_coefficients()
        
    def _generate_fourier_coefficients(self):
        """Generate Fourier basis coefficients"""
        # Generate all combinations of coefficients up to fourier_order
        # Limit to reasonable number of features
        max_features = min(self.n_features, 500)  # Cap at 500 features
        
        self.fourier_coeffs = []
        
        # Generate coefficients using itertools for proper combinations
        import itertools
        for coeffs in itertools.product(range(self.fourier_order + 1), repeat=self.fourier_state_dim):
            if len(self.fourier_coeffs) >= max_features:
                break
            self.fourier_coeffs.append(list(coeffs))
        
        self.fourier_coeffs = np.array(self.fourier_coeffs)
        self.n_features = len(self.fourier_coeffs)  # Update to actual number
        
        # Reinitialize weights and traces with correct dimensions
        self.weights = np.zeros((self.n_actions, self.n_features))
        self.traces = np.zeros((self.n_actions, self.n_features))
        
    def _fourier_features(self, state):
        """Compute Fourier basis features for state"""
        if isinstance(state, (int, float)):
            state = np.array([state])
        state = np.array(state).flatten()
        
        # Use only first fourier_state_dim dimensions if state is larger
        if len(state) > self.fourier_state_dim:
            # Use PCA or select most important features
            # For now, just take first N dimensions
            state = state[:self.fourier_state_dim]
        elif len(state) < self.fourier_state_dim:
            # Pad with zeros if state is smaller
            state = np.pad(state, (0, self.fourier_state_dim - len(state)))
        
        # Normalize state to [0, 1]
        try:
            low = self.observation_space.low[:self.fourier_state_dim]
            high = self.observation_space.high[:self.fourier_state_dim]
            normalized = (state - low) / (high - low + 1e-8)
        except:
            normalized = state
            
        normalized = np.clip(normalized, 0, 1)
        
        # Compute features
        features = np.cos(np.pi * np.dot(self.fourier_coeffs, normalized))
        return features
        
    def _q_value(self, state, action):
        """Compute Q-value for state-action pair"""
        features = self._fourier_features(state)
        return np.dot(self.weights[action], features)
        
    def act(self, state):
        """Select action using epsilon-greedy policy"""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.n_actions)
        else:
            q_values = [self._q_value(state, a) for a in range(self.n_actions)]
            return np.argmax(q_values)
            
    def learn(self, state, action, reward, next_state, done):
        """Update weights using True Online SARSA(λ)"""
        # Get features
        features = self._fourier_features(state)
        next_features = self._fourier_features(next_state)
        
        # Get next action (for SARSA)
        next_action = self.act(next_state) if not done else 0
        
        # Compute TD error
        q_current = np.dot(self.weights[action], features)
        q_next = np.dot(self.weights[next_action], next_features) if not done else 0
        delta = reward + self.gamma * q_next - q_current
        
        # Update eligibility traces
        self.traces[action] = self.gamma * self.lamb * self.traces[action] + features
        
        # Update weights
        self.weights[action] += self.alpha * delta * self.traces[action]
        
        # Decay traces if terminal
        if done:
            self.traces = np.zeros_like(self.traces)
    
    def save(self, filepath):
        """Save trained agent to file"""
        import pickle
        agent_data = {
            'weights': self.weights,
            'fourier_coeffs': self.fourier_coeffs,
            'n_features': self.n_features,
            'alpha': self.alpha,
            'gamma': self.gamma,
            'epsilon': self.epsilon,
            'lamb': self.lamb,
            'fourier_order': self.fourier_order,
            'state_dim': self.state_dim,
            'original_state_dim': self.original_state_dim,
            'fourier_state_dim': self.fourier_state_dim,
            'n_actions': self.n_actions,
        }
        with open(filepath, 'wb') as f:
            pickle.dump(agent_data, f)
        print(f"Agent saved to {filepath}")
    
    @classmethod
    def load(cls, filepath, observation_space, action_space):
        """Load trained agent from file"""
        import pickle
        with open(filepath, 'rb') as f:
            agent_data = pickle.load(f)
        
        # Create agent with saved parameters
        agent = cls(
            observation_space=observation_space,
            action_space=action_space,
            alpha=agent_data['alpha'],
            gamma=agent_data['gamma'],
            epsilon=agent_data['epsilon'],
            lamb=agent_data['lamb'],
            fourier_order=agent_data['fourier_order']
        )
        
        # Restore trained weights and coefficients
        agent.weights = agent_data['weights']
        agent.fourier_coeffs = agent_data['fourier_coeffs']
        agent.n_features = agent_data['n_features']
        agent.original_state_dim = agent_data['original_state_dim']
        agent.fourier_state_dim = agent_data['fourier_state_dim']
        agent.traces = np.zeros_like(agent.weights)
        
        print(f"Agent loaded from {filepath}")
        return agent
