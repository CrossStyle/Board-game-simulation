import argparse
import copy
import numpy as np
from MTCSPlayer import MTCSPlayer, task_duration
import pandas as pd
import time
from precedence_graph import precedence_graph


class Board:
    def __init__(self, init_game_state, players):
        self.current_game_state = init_game_state
        self.current_game_state['backup'] = set()
        self.current_game_state['done'] = set()
        self.record = {}
        self.idle = {}

        self.availables = copy.deepcopy(self.current_game_state['init'])

        self.task_his = []

        self.players = players
        self.current_active_players = [player.id for player in self.players]
        self.current_player = None
        self.start_player_id = 0

        self.counter = 0
        self.new_record()

    def new_record(self):
        if self.counter not in self.record.keys():
            self.record[self.counter] = {}


    def run_step(self):
        step = min([p.duration for p in self.players])
        for _ in range(step):
            self.record[self.counter] = {}
            for player in self.players:
                self.record[self.counter][player.task] = player.id
            self.counter += 1
        self.check_availability_step(step)

    def check_availability(self):
        self.current_active_players = []
        for player in self.players:
            player.work()
            if player.duration <= 0:
                self.current_active_players.append(player.id)
                self.update_task_state(player.task)

        if self.current_active_players:
            for task in self.current_game_state['backup']:
                rel_tasks = self.current_game_state['b_rel'][task]
                if rel_tasks <= self.current_game_state['done']:
                    if task not in self.availables:
                        if task not in self.task_his:
                            self.availables.append(task)

    def check_availability_step(self, step):
        self.current_active_players = []
        for player in self.players:
            player.work_step(step)
            if player.duration <= 0:
                self.current_active_players.append(player.id)
                if player.task:
                    self.update_task_state(player.task)

        if self.current_active_players:
            for task in self.current_game_state['backup']:
                rel_tasks = self.current_game_state['b_rel'][task]
                if rel_tasks <= self.current_game_state['done']:
                    if task not in self.availables:
                        if task not in self.task_his:
                            self.availables.append(task)

    def update_task_state(self, task):
        next_tasks = self.current_game_state['f_rel'][task]
        self.current_game_state['backup'].update(next_tasks)
        self.current_game_state['done'].add(task)
        self.current_game_state['backup'] = self.current_game_state['backup'] - self.current_game_state['done'].intersection(self.current_game_state['backup'])
        if task in self.current_game_state['left']:
            self.current_game_state['left'].remove(task)

    def do_move(self, task, show_log=False):
        self.task_his.append(task)
        if show_log:
            print('#########################################')
            print(self.counter, ' input task: ', task)
            print('available tasks: ', self.availables)

        while True:
            if self.current_active_players:
                break
            else:
                self.run_step()

        if self.start_player_id in self.current_active_players:
            self.current_player = self.players[self.start_player_id]
            self.current_active_players.remove(self.start_player_id)
        else:
            self.current_player = self.players[self.current_active_players.pop()]

        # assign task to agent
        self.players[self.current_player.id].assign_task(task, task_duration[task[0]])

        if task in self.availables:
            self.availables.remove(task)
        end, _ = self.game_end()
        while not end:
            if self.availables:
                break
            step_list = []
            working_players = []
            for player in self.players:
                if player.duration > 0:
                    step_list.append(player.duration)
                    working_players.append(player.id)

            step = min(step_list)
            for _ in range(step):
                self.record[self.counter] = {}
                for id in working_players:
                    working_player = self.players[id]
                    self.record[self.counter][working_player.task] = id
                self.counter += 1
            self.check_availability_step(step)
            end, _ = self.game_end()
        if end:
            self.check_idle()

    def game_end(self):
        if not self.current_game_state['left']:
            return True, self.counter
        else:
            return False, self.counter

    def check_idle(self):
        idle = 0
        player_num = len(self.players)
        for item in self.record.values():
            if item:
                idle += player_num - len(item)
        self.idle['total'] = idle
        self.idle['average_idle'] = idle / player_num


def rollout_policy_fn(board):
    """a coarse, fast version of policy_fn used in the rollout phase."""
    # rollout randomly
    action_probs = np.random.rand(len(board.availables))
    return zip(board.availables, action_probs)


class MultiPlayerGame:
    def __init__(self, game_state, player_num, c, round_num):
        self.board = None
        self.player_num = player_num
        self.players = []
        self.c = c
        self.round_num = round_num
        self.game_structure = game_state
        self.init_game()

    def init_game(self):
        for player_id in range(self.player_num):
            self.players.append(MTCSPlayer(player_id, 'human', self.c, self.round_num))
        self.board = Board(self.game_structure, self.players)


def load_game_data(xlsx_path, init):
    df = pd.read_excel(xlsx_path, header=None, dtype=str)
    forward_dict = {}
    reverse_dict = {}
    all_stone = set()
    for index, row in df.iterrows():
        forward_dict[row[0]] = set()
        for r_idx, item in enumerate(row):
            if not pd.isna(item):
                all_stone.add(item)
                if r_idx > 0:
                        forward_dict[row[0]].add(item)
                        if item not in reverse_dict.keys():
                            reverse_dict[item] = set()
                        reverse_dict[item].add(row[0])
    game_state = {"f_rel": forward_dict, "b_rel": reverse_dict, 'init': list(init), 'left': all_stone-init}
    return game_state


def parse_args():
    parser = argparse.ArgumentParser(description='Train a action recognizer')
    parser.add_argument('--total_game', default=1, type=int, help='Number of games to play')
    parser.add_argument('--player_num', default=8, type=int, help='Number of players of the same type')
    parser.add_argument('--N', default=10, type=int, help='Number of simulations per round N')
    parser.add_argument('--C', default=10, type=int, help='Parameter for balancing utilization and exploration C')
    parser.add_argument('--scaffold_type', default='2x10', type=str, help='Structure of scaffold')
    return parser.parse_args()


def run():
    args = parse_args()
    total_game = args.total_game
    player_num = args.player_num
    round_num =args. N
    c = args.C
    scaffold_type = args.scaffold_type

    print('player_num: ', player_num)
    print('total_game: ', total_game)
    print('C: ', c, ' round_num: ', round_num)
    print('type: ', scaffold_type)

    start_player = 0
    total_time, idle_time = [], []
    computational_time = []
    agent_utilization = []

    best_used_time = 1e13
    best_model = None

    for _ in range(total_game):
        t1 = time.perf_counter()
        init_state = precedence_graph[scaffold_type][0]
        GAME_STATE = load_game_data(precedence_graph[scaffold_type][1], init_state)

        wrc_game = MultiPlayerGame(GAME_STATE, player_num, c, round_num)
        player = wrc_game.players[start_player]
        limit = 1000
        for i in range(limit):
            end, used_time = wrc_game.board.game_end()
            if end:
                t2 = time.perf_counter()
                c_time = t2 - t1
                computational_time.append(c_time)
                print('used time: ', c_time)
                print('cost: ', used_time)
                total_time.append(used_time)
                idle_time.append(wrc_game.board.idle['total'])
                agent_utilization.append(1 - wrc_game.board.idle['average_idle'] / wrc_game.board.counter)
                print('Agent usage: ', 1 - wrc_game.board.idle['average_idle'] / wrc_game.board.counter)
                if used_time < best_used_time:
                    best_used_time = used_time
                    best_model = copy.deepcopy(wrc_game)
                break
            sensible_moves = wrc_game.board.availables
            if len(sensible_moves) > 0:
                move = player.mcts.get_move(wrc_game.board)
                player.mcts.update_with_move(move)
                wrc_game.board.do_move(move, False)

    print(player_num, ' player setting computational time', np.mean(computational_time), ' std: ', np.std(computational_time))
    print(player_num, ' player setting best cost', min(total_time))
    print(player_num, ' average cost', np.mean(total_time), ' std: ', np.std(total_time))
    print('Average idle time: ', np.mean(idle_time)/player_num)
    print('Average agent usage: ', 1-np.mean(idle_time)/(np.mean(total_time)*player_num))
    return best_model


if __name__ == "__main__":
    best_model = run()





