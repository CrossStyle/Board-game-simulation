import argparse
import copy
import time
from multi_tasking_team import Board, load_game_data
import numpy as np
from random import choice
from precedence_graph import precedence_graph
from MTCSPlayer import MTCSPlayer, task_duration


class WRCChess(Board):
    def __init__(self, init_game_state, players, h_ids, r_ids, r_tasks, h_tasks):
        super(WRCChess, self).__init__(init_game_state, players)
        self.h_ids = h_ids
        self.r_ids = r_ids
        self.r_tasks = r_tasks
        self.h_tasks = h_tasks
        self.active_robot = set(r_ids)
        self.active_human = set(h_ids)
        self.his_state = []
        self.next_player = None
        self.robot_availables = [task for task in self.availables if task[0] in self.r_tasks]
        self.human_availables = [task for task in self.availables if task[0] in self.h_tasks]
        self.new_availables = []
        self.available_his = None


    def update_agent_state(self):
        self.active_human = []
        self.active_robot = []

        for player in self.players:
            player.work()
            if player.duration <= 0:
                if player.task:
                    self.update_task_state(player.task)
                if player.type == 'robot':
                    self.active_robot.append(player.id)
                else:
                    self.active_human.append(player.id)

    def update_agent_state_step(self):
        step_list = []
        working_players = []
        step = None
        for player in self.players:
            if player.duration > 0:
                step_list.append(player.duration)
                working_players.append(player.id)

        if step_list:
            step = min(step_list)
            for _ in range(step):
                self.record[self.counter] = {}
                for id in working_players:
                    working_player = self.players[id]
                    self.record[self.counter][working_player.task] = id
                self.counter += 1

        for player_id in working_players:
            player = self.players[player_id]
            if step:
                player.work_step(step)
            if player.duration <= 0:
                # self.current_active_players.append(player.id)
                if player.task:
                    self.update_task_state(player.task)
                if player.type == 'robot':
                    self.active_robot.add(player.id)
                else:
                    self.active_human.add(player.id)

    # def check_task_type(self, task):
    #     if task[0] in self.r_tasks:
    #         task_type = 'Robot'
    #     else:
    #         task_type = 'Human'
    #     return task_type

    def game_end(self):
        if not self.current_game_state['left']:
            return True, self.counter
        else:
            return False, self.counter


    def update_available_fast(self):
        potential_tasks = self.current_game_state['backup']
        for task in potential_tasks:
            rel_tasks = self.current_game_state['b_rel'][task]
            if rel_tasks <= self.current_game_state['done']:
                if task not in self.availables:
                    if task not in self.task_his:
                        self.availables.append(task)
                        self.new_availables.append(task)

    def update_agent_available(self):
        potential_stones = self.new_availables
        if self.new_availables:
            for task in potential_stones:
                if task[0] in task_constraints['humanoid']:
                    self.human_availables.append(task)
                if task[0] in task_constraints['robot']:
                    self.robot_availables.append(task)
            self.available_his = self.availables[:]
            self.new_availables = []

    def fit_task(self):
        available = set(i[0] for i in self.availables)

        marker = -1
        hf, rf = False, False
        if self.active_human:
            h = task_constraints['humanoid']
            hf = list(available & h)
            if hf:
                marker = 0

        if self.active_robot:
            r = task_constraints['robot']
            rf = list(available & r)
            if rf:
                marker = 1

        if hf and rf:
            marker = 2
        return marker

    def do_move(self, task, show_log=False):
        self.task_his.append(task)

        if show_log:
            print('#########################################')
            print(self.counter, ' input task: ', task)
            print('available tasks: ', self.availables)

        # assign task to agent
        self.players[self.current_player.id].assign_task(task, task_duration[task[0]])
        if self.available_his:
            self.availables = self.available_his
        self.availables.remove(task)
        if task in self.current_game_state['init']:
            self.current_game_state['init'].remove(task)

        if task in self.human_availables:
            self.human_availables.remove(task)
        if task in self.robot_availables:
            self.robot_availables.remove(task)

        if self.current_player.type == 'humanoid':
            self.active_human.remove(self.current_player.id)
        else:
            self.active_robot.remove(self.current_player.id)

        # self.update_available()
        end, _ = self.game_end()
        while True:
            marker = self.fit_task()
            if marker >= 0 or end:
                break
            else:
                self.update_agent_state_step()
                self.update_available_fast()
                end, _ = self.game_end()

        # determine next player
        if marker == 0:
            next_id = choice(list(self.active_human))
        elif marker == 1:
            next_id = choice(list(self.active_robot))
        else:
            next_id = choice(list(self.active_human)+list(self.active_robot))

        self.current_player = self.players[next_id]
        self.update_agent_available()

        if self.current_player.type == 'humanoid':
            self.availables = self.human_availables[:]
        else:
            self.availables = self.robot_availables[:]

        end, _ = self.game_end()
        if end:
            self.check_idle()

    def check_idle(self):
        idle = 0
        h_idle = 0
        r_idle = 0
        player_num = len(self.players)
        for item in self.record.values():
            if item:
                idle += player_num - len(item)

                # check human idle
                if self.h_ids:
                    h_tmp = 0
                    for h_id in self.h_ids:
                        if h_id in item.values():
                            h_tmp += 1
                    h_idle += len(self.h_ids) - h_tmp

                # check robot idle
                if self.r_ids:
                    r_tmp = 0
                    for r_id in self.r_ids:
                        if r_id in item.values():
                            r_tmp += 1
                    r_idle += len(self.r_ids) - r_tmp

        self.idle['total'] = idle
        self.idle['average_idle'] = idle / player_num

        if self.h_ids:
            self.idle['human'] = h_idle / len(self.h_ids)
        if self.r_ids:
            self.idle['robot'] = r_idle / len(self.r_ids)

    def get_current_player(self):
        return self.current_player


class WRCGame:
    def __init__(self, game_state, human_player_num, robot_player_num, c, round_num):
        self.board = None
        self.robot_player_num = robot_player_num
        self.human_player_num = human_player_num
        self.players = []
        self.c = c
        self.round_num = round_num
        self.game_structure = game_state
        self.init_game()

    def init_game(self):
        for h_id in range(self.human_player_num):
            self.players.append(MTCSPlayer(h_id, 'humanoid', self.c, self.round_num))
        h_ids = [i for i in range(self.human_player_num)]
        for r_id in range(self.human_player_num, self.human_player_num + self.robot_player_num):
            self.players.append(MTCSPlayer(r_id, 'robot', self.c, self.round_num))
        r_ids = [i for i in range(self.human_player_num, self.human_player_num + self.robot_player_num)]
        self.board = WRCChess(self.game_structure, self.players, h_ids, r_ids, task_constraints['robot'], task_constraints['humanoid'])


def run():
    args = parse_args()
    total_game = args.total_game
    humanoid_player_num = args.humanoid_num
    robot_player_num = args.robot_num
    round_num = args.N
    c = args.C
    scaffold_type = args.scaffold_type

    print('total_game: ', total_game)
    print('C: ', c, ' round_num: ', round_num)
    print('type: ', scaffold_type)

    if len(task_constraints['humanoid']) < 8:
        print(humanoid_player_num, 'I-', robot_player_num, 'R')
    else:
        print(humanoid_player_num, 'M-', robot_player_num, 'R')

    start_player = humanoid_player_num  # 0
    total_time, idle_time = [], []
    agent_utilization = []
    c_time = []

    best_used_time = 1e13
    best_model = None
    for _ in range(total_game):
        t1 = time.perf_counter()

        init_state = precedence_graph[scaffold_type][0]
        GAME_STATE = load_game_data(precedence_graph[scaffold_type][1], init_state)

        wrc_game = WRCGame(GAME_STATE,
                           human_player_num=humanoid_player_num,
                           robot_player_num=robot_player_num,
                           c=c,
                           round_num=round_num)
        wrc_game.board.current_player = wrc_game.board.players[start_player]

        while True:
            player_in_turn = wrc_game.board.get_current_player()
            move = player_in_turn.get_action(wrc_game.board)
            wrc_game.board.do_move(move, False)
            end, used_time = wrc_game.board.game_end()
            if end:
                t2 = time.perf_counter()
                com_time = t2 - t1
                c_time.append(com_time)
                print('used time: ', com_time)
                print('cost: ', used_time)

                total_time.append(used_time)
                agent_utilization.append(1 - wrc_game.board.idle['average_idle'] / wrc_game.board.counter)
                print('Agent usage: ', 1 - wrc_game.board.idle['average_idle'] / wrc_game.board.counter)
                idle_time.append(wrc_game.board.idle['total'])
                if used_time < best_used_time:
                    best_used_time = used_time
                    best_model = copy.deepcopy(wrc_game)
                break

    print('best cost', best_model.board.counter)
    print('computational time', np.mean(c_time), ' std: ', np.std(c_time))
    print('average cost', np.mean(total_time), ' std: ', np.std(total_time))
    print('Best agent usage: ', 1 - best_model.board.idle['average_idle'] / best_model.board.counter)
    print('Average agent usage: ', np.mean(agent_utilization))
    return best_model


def parse_args():
    parser = argparse.ArgumentParser(description='Train a action recognizer')
    parser.add_argument('--total_game', default=1, type=int, help='Number of games to play')

    parser.add_argument('--humanoid_num', default=5, type=int, help='Number of humanoid robots (powerful)')
    parser.add_argument('--robot_num', default=3, type=int, help='Number of general transportation robots (less powerful)')

    parser.add_argument('--N', default=10, type=int, help='Number of simulations per round N')
    parser.add_argument('--C', default=10, type=int, help='Parameter for balancing utilization and exploration C')
    parser.add_argument('--scaffold_type', default='2x10', type=str, help='Structure of scaffold')
    return parser.parse_args()


if __name__ == '__main__':
    task_constraints = {
        'humanoid': {'C', 'D', 'F', 'H'},
        # 'humanoid': {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'}
        'robot': {'A', 'B', 'E', 'G'}}
    best_model = run()
