# Multi-player board game

This is implementation of MCTS-based multi-player board game.

## Requirement

```
pandas
numpy
```

## Usage

1. Multi-tasking robotic team with the same robot type: Robot can handle all types of activities from A to H

```
python multi_tasking_team.py 
--total_game <Number of games to play> 
--player_num <Number of players of the same type> 
--N <Number of simulations per round> 
--C <Parameter for balancing utilization and exploration>
--scaffold_type <2x1|2x2|2x4|2x6|2x8|2x10>
```

For example, 1 game, 3 robots, and 2 story 2 span scaffold

```
python multi_tasking_team.py --total_game 1 --player_num 3 --N 50 --C 10 --scaffold_type 2x2
```

2. Mixed robotic team with two different types of robots: Installation robots [C D F H] and transportation robots [A B E G]

```
python mixed_team.py 
--total_game <Number of games to play> 
--humanoid_num <Number of humanoid robots> 
--robot_num <Number of general transportation robots> 
--N <Number of simulations per round> 
--C <Parameter for balancing utilization and exploration>
--scaffold_type <2x1|2x2|2x4|2x6|2x8|2x10>
```

For example, 1 game, 2 installation robots, 1 transportation robots, and 2 story 2 span scaffold

```
python mixed_team.py --total_game 1 --humanoid_num 2 --robot_num 1 --N 50 --C 10 --scaffold_type 2x2
```

