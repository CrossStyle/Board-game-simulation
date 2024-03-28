import numpy as np
from operator import itemgetter
import _pickle as cPickle


task_duration = {
    'A': 5,
    'B': 10,
    'C': 4,
    'D': 8,
    'E': 5,
    'F': 20,
    'G': 10,
    'H': 5,
}


def rollout_policy_fn(board):
    """a coarse, fast version of policy_fn used in the rollout phase."""
    # rollout randomly
    action_probs = np.random.rand(len(board.availables))
    return zip(board.availables, action_probs)


def policy_value_fn(board):
    """a function that takes in a state and outputs a list of (action, probability)
    tuples and a score for the state"""
    # return uniform probabilities and 0 score for pure MCTS
    action_probs = np.ones(len(board.availables))/len(board.availables)
    return zip(board.availables, action_probs), 0


class TreeNode(object):
    """A node in the MCTS tree. Each node keeps track of its own value Q,
    prior probability P, and its visit-count-adjusted prior score u.
    """

    def __init__(self, parent, prior_p):
        self.parent = parent
        self.children = {}  # a map from action to TreeNode
        self.n_visits = 0
        self.Q = 0
        self.u = 0
        self.P = prior_p

    def expand(self, action_priors):
        """Expand tree by creating new children.
        action_priors: a list of tuples of actions and their prior probability
            according to the policy function.
        """
        for action, prob in action_priors:
            if action not in self.children:
                self.children[action] = TreeNode(self, prob)

    def select(self, c_puct):
        """Select action among children that gives maximum action value Q
        plus bonus u(P).
        Return: A tuple of (action, next_node)
        """
        data = {}
        for k, v in self.children.items():
            data[k] = [v.get_value(c_puct), v]
        return data
        # return max(self.children.items(), key=lambda act_node: act_node[1].get_value(c_puct))

    def update(self, leaf_value):
        """Update node values from leaf evaluation.
        leaf_value: the value of subtree evaluation from the current player's
            perspective.
        """
        # Count visit.
        self.n_visits += 1
        # Update Q, a running average of values for all visits.
        self.Q += 1.0*(leaf_value - self.Q) / self.n_visits

    def update_recursive(self, leaf_value):
        """Like a call to update(), but applied recursively for all ancestors.
        """
        # If it is not root, this node's parent should be updated first.
        if self.parent:
            self.parent.update_recursive(leaf_value)
        self.update(leaf_value)

    def get_value(self, c_puct):
        """Calculate and return the value for this node.
        It is a combination of leaf evaluations Q, and this node's prior
        adjusted for its visit count, u.
        c_puct: a number in (0, inf) controlling the relative impact of
            value Q, and prior probability P, on this node's score.
        """
        self.u = (c_puct * self.P * np.sqrt(self.parent.n_visits) / (1 + self.n_visits))
        return self.Q + self.u

    def is_leaf(self):
        """Check if leaf node (i.e. no nodes below this have been expanded).
        """
        return self.children == {}

    def is_root(self):
        return self.parent is None


class MCTS(object):
    """A simple implementation of Monte Carlo Tree Search."""

    def __init__(self, policy_value_fn, c_puct=5, n_playout=10000):
        """
        policy_value_fn: a function that takes in a board state and outputs
            a list of (action, probability) tuples and also a score in [-1, 1]
            (i.e. the expected value of the end game score from the current
            player's perspective) for the current player.
        c_puct: a number in (0, inf) that controls how quickly exploration
            converges to the maximum-value policy. A higher value means
            relying on the prior more.
        """
        self.root = TreeNode(None, 1.0)
        self.policy = policy_value_fn
        self.c_puct = c_puct
        self.n_playout = n_playout

    def _playout(self, state):
        """Run a single playout from the root to the leaf, getting a value at
        the leaf and propagating it back through its parents.
        State is modified in-place, so a copy must be provided.
        """
        node = self.root
        while(1):
            if node.is_leaf():
                break
            # Greedily select next move.
            data = node.select(self.c_puct)
            data = sorted(data.items(), key=lambda kv: kv[1][0])

            while data:
                action, (r, node) = data.pop()
                if action in state.availables:
                    break
                else:
                    action = state.availables[0]
                    if action in self.root.children.keys():
                        node = self.root.children[action]
                    else:
                        node = TreeNode(self.root, 1/(len(self.root.children)+1))

            state.do_move(action)
        action_probs, _ = self.policy(state)
        # Check for end of game
        end, used_time = state.game_end()
        if not end:
            node.expand(action_probs)
        # Evaluate the leaf node by random rollout
        leaf_value = self._evaluate_rollout(state)
        # Update value and visit count of nodes in this traversal.
        node.update_recursive(-leaf_value)

    def _evaluate_rollout(self, state, limit=1000):
        """Use the rollout policy to play until the end of the game,
        returning used_time.
        """
        for i in range(limit):
            end, used_time = state.game_end()
            if end:
                break
            action_probs = rollout_policy_fn(state)
            max_action = max(action_probs, key=itemgetter(1))[0]
            # print(max_action)
            state.do_move(max_action)
        else:
            # If no break from the loop, issue a warning.
            print("WARNING: rollout reached move limit")
        return used_time

    def get_move(self, state):
        """Runs all playouts sequentially and returns the most visited action.
        state: the current game state

        Return: the selected action
        """
        for n in range(self.n_playout):
            # state_copy = copy.deepcopy(state)
            state_copy = cPickle.loads(cPickle.dumps(state))
            self._playout(state_copy)
        return max(self.root.children.items(), key=lambda act_node: act_node[1].n_visits)[0]

    def update_with_move(self, last_move):
        """Step forward in the tree, keeping everything we already know
        about the subtree.
        """
        if last_move in self.root.children:
            self.root = self.root.children[last_move]
            self.root.parent = None
        else:
            self.root = TreeNode(None, 1.0)

    def __str__(self):
        return "MCTS"


class MTCSPlayer:
    """AI player based on MCTS"""
    def __init__(self, player_id, agent_type, c_puct=50, n_playout=1000):
        self.task = None
        # self.active = None
        self.duration = 0
        self.mcts = MCTS(policy_value_fn, c_puct, n_playout)
        self.id = player_id
        self.type = agent_type

    def set_availability(self, active):
        self.active = active

    def assign_task(self, task, duration):
        self.set_availability(False)
        self.duration = duration
        self.task = task

    def reset_player(self):
        self.mcts.update_with_move(-1)

    def get_action(self, board):
        sensible_moves = board.availables
        if len(sensible_moves) > 0:
            move = self.mcts.get_move(board)
            self.mcts.update_with_move(-1)
            return move
        else:
            print("WARNING: all the stones are taken")

    def work(self):
        self.duration -= 1

    def work_step(self, step):
        self.duration -= step
