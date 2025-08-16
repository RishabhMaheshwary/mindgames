COLONEL_BOLOTTO = """
<game>
{game_state}
</game>

{prior_actions}

Given the game state above, past games between you and opponent (if any), your & opponent's actions (if any), generate all combinatorial possible moves possible distinct moves for the next turn that will lead to a win.

- Use logical deduction and enumeration to explore every distinct valid action or move combination for the current game state.
- Output your reasoning in <think> </think> tags.
- Then, suggest all  distinct possible combination of valid moves in the required format in <action> </action> tags. 
- Make sure to output diverse moves, so as to explore far points in the search space better.
- If unsure or you choose to wait, output <action>pass</action>.

Output format:
<think> ...your reasoning... </think>
<action> ... </action>
<action> ... </action>
<action> ... </action>

Example:

Try to be diverse in allocating resources like exploring far away points in the search space better as below
<action>
[A6 B7 C7]
</action>
<action>
[A10 B0 C10]
</action>
"""

TPID = """
<game>
{game_state}
</game>

{prior_actions}

Given the game state, past rounds between you and other two opponent (if any), your & opponent's actions (if any), generate possible distinct moves for the next turn that will lead to a win.


- Output your reasoning in <think> </think> tags.
- Then, suggest distinct moves in the required format in <action> </action> tags. 
- Make sure to output diverse moves, so as to explore far points in the search space better.
- If unsure or you choose to wait, output <action>pass</action>.


Output format:
<think> ...your reasoning... </think>
<action> ... </action>
<action> ... </action>
<action> ... </action>

Example:

If it asks that you can freely converse for the next 1 round, chat with other players freely.
Else if it asks to submt your decisions, use the format <action>[pid_opponent1 action1] [pid_opponent2 action2]</action>. For example if you are player 1
<action>
Let's all cooperate to maximize scores.
</action>
<action>
[0 cooperate] [2 defect]
</action>
<action>
[0 defect] [2 defect]
</action>
"""

CODENAMES = """
<game>
{game_state}
</game>

{prior_actions}

Given the current game state of the board and the sequence of actions (if any), generate possible distinct moves for the next turn.

- If you are a spymaster of your team, do NOT give a clue that is a subset/exact match of words on the board. 
- Give a clue that AVOIDS, opponent words, neutral words and the assassin.
- If you have to guess words, guess from the words on the board only.
- Output your reasoning in <think> </think> tags.
- Then, suggest all distinct moves in the required format in <action> </action> tags. 
- Make sure to output diverse & multiple distinct moves, so as to explore the search space better.
- If unsure or you choose to wait, output <action>pass</action>.

Output format:
<think> ...your reasoning... </think>
<action> ... </action>
<action> ... </action>
<action> ... </action>

Example: 
<action>
[fire 2]
</action>
<action>
[rice, grain]
</action>
"""


COLONEL_BOLOTTO_OPPONENT = """
<game>
{game_state}
</game>

{prior_actions}

Given game state, the previous games played (if any), your & opponent's move (if any), generate all combinatorial possible opponent moves to decide every possible combination of valid moves for the next turn.

- Begin by reasoning in <think> </think> tags.
- Then, list each valid and distinct possible opponent move in separate <opponent_action> </opponent_action> tags.
- Think carefully about all valid combinations based on the game rules and current state.
- Make sure to output many distinct moves, so as to far points in the search space better.
- If the opponent might skip a turn or is unsure, include <opponent_action>pass</opponent_action>.

Output format:
<think> ...opponent reasoning... </think>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>

Example:

Try to be diverse in allocating resources like exploring far away points in the search space better as below.
<opponent_action>
[A4 B8 C8]
</opponent_action>
<opponent_action>
[A10 B10 C0]
</opponent_action>
"""

TPID_OPPONENT = """
<game>
{game_state}
</game>

{prior_actions}

Given the game state, previous rounds (if any), your & opponent's move (if any), generate next possible opponent moves.

- First identify the player ids of your opponent and then think about there actions in <think> </think> tags.
- Then add each scenario containing both opponent's move in the <opponent_action> </opponent_action> tag. 
- Add different scenarios in different <opponent_action> </opponent_action> tags.
- Think carefully about all combinations based on the game rules and current state.
- Make sure to output many distinct scenarios.
- If the opponent might skip a turn or is unsure, include <opponent_action>pass</opponent_action>.


Output format:
<think> ...opponent reasoning... </think>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>

Example:

If it asks that you can freely converse for the next 1 round, coverse within <opponent_action> </opponent_action> tags like:
<opponent_action>Let's all cooperate for everyone's benefit.</opponent_action>.

Else give actions as shown below:

For example if you are player 1 then for opponents 0 and 2 example output can be like below.
<opponent_action>
Player 0 cooperates with Player 1 and defects against Player 2. Player 2 cooperates with Player 0 but defects against Player 1
</opponent_action>
<opponent_action>
Player 0 defects against Player 1 and cooperates against Player 2. Player 2 defects against Player 0 but cooperates against Player 1
</opponent_action>
"""

CODENAMES_OPPONENT = """
<game>
{game_state}
</game>

{prior_actions}

Given the current board state, the sequence of actions so far, generate possible distinct moves by the opponent's spymaster's for the next tun.

- Begin by reasoning in <think> </think> tags.
- Do NOT give a clue that is a subset/exact match of words on the board.
- Give a clue that AVOIDS, opponent words, neutral words and the assassin.
- Then, list valid and distinct possible opponent move in separate <opponent_action> </opponent_action> tags.
- Make sure to output diverse & multiple distinct opponent moves, so as to explore the search space better.
- If the opponent might skip a turn or is unsure, include <opponent_action>pass</opponent_action>.

Output format:
<think> ...opponent reasoning... </think>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>

Example:

<opponent_action>
[fire 2]
</opponent_action>
<opponent_action>
[cloud 1]
</opponent_action>
"""

EVAL_PROMPT_TEMPLATE = """You are evaluating multiple simulated game-outcomes, all starting from the same base state. Decide which “future” is most likely to lead to victory for your side.

<base_game_state>
{base_state}
</base_game_state>

<futures>
{futures_blocks}
</futures>

Output:
1. Your reasoning in <think>…</think>  
2. Exactly one chosen future in [[index]] where index is the 1-based index of that block. For example, [[4]].

"""


PAIRWISE_EVAL_PROMPT_TEMPLATE = """You are comparing exactly two simulated futures that both start from the same base state.
Your goal is to decide which future is more likely to lead to a higher final reward for the player who makes moves within <action> </action> tags. If a future does not have complete information, skip it. Assume rational opponents and standard play unless the futures indicate otherwise.

<base_game_state>
{base_state}
</base_game_state>

<future_1>
{future_1}
</future_1>

<future_2>
{future_2}
</future_2>

Output:
1) Your concise reasoning in <think>…</think>
2) Exactly one choice in [[1]] or [[2]] indicating which future you prefer overall. If there is a tie, output [[tie]].
"""



NEXT_STEP_PROMPT_TEMPLATE = """You are playing a game. Given the current game state and the sequence of prior actions (if any), generate all combinatorial possible moves to decide every possible combination of valid moves for the next turn that will lead to a win.

- Use logical deduction and enumeration to explore every distinct valid action or move combination for the current game state.
- Output your reasoning in <think> </think> tags.
- Then, suggest all  distinct possible combination of valid moves in the required format in <action> </action> tags. 
- Make sure to output distinct moves, so as to explore far points in the search space better, but in decreasing order of success probability, i.e the first move should be the most likely to lead to a win
- If unsure or you choose to wait, output <action>pass</action>.

Input format:
<game_state>{game_state}</game_state>
<prior_actions>{prior_actions}</prior_actions>

Output format:
<think> ...your reasoning... </think>
<action> ... </action>
<action> ... </action>
<action> ... </action>
"""

OPPONENT_MOVE_PROMPT_TEMPLATE = """You are simulating your opponent's next move. Given the current game state, the sequence of actions so far (if any), and the last move by you (if any), generate all combinatorial possible opponent moves to decide every possible combination of valid moves for the next turn.

- Begin by reasoning in <think> </think> tags.
- Then, list each valid and distinct possible opponent move in separate <opponent_action> </opponent_action> tags.
- Think carefully about all valid combinations based on the game rules and current state.
- Make sure to output many distinct moves, so as to far points in the search space better, but in decreasing order of success probability, i.e the first move should be the most likely to lead to a win.
- If the opponent might skip a turn or is unsure, include <opponent_action>pass</opponent_action>.

Input format:
game_state: {game_state}
prior_actions: {prior_actions}
last_move_by_you: {last_move}

Output format:
<think> ...opponent reasoning... </think>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>
"""

NEXT_STEP_PROMPT_TEMPLATE = """You are playing a game. Given the current game state and the sequence of prior actions (if any), generate possible distinct moves for the next turn.

- Output your reasoning in <think> </think> tags.
- Then, suggest all distinct moves in the required format in <action> </action> tags. 
- Make sure to output diverse & multiple distinct moves, so as to explore the search space better.
- If unsure or you choose to wait, output <action>pass</action>.

Input format:
<game_state>{game_state}</game_state>
<prior_actions>{prior_actions}</prior_actions>

Output format:
<think> ...your reasoning... </think>
<action> ... </action>
<action> ... </action>
<action> ... </action>
"""

OPPONENT_MOVE_PROMPT_TEMPLATE = """You are simulating your opponent's next move. Given the current game state, the sequence of actions so far, and the last move by you (if any), generate possible distinct moves by the opponent for the next turn.

- Begin by reasoning in <think> </think> tags.
- Then, list valid and distinct possible opponent move in separate <opponent_action> </opponent_action> tags.
- Make sure to output diverse & multiple distinct opponent moves, so as to explore the search space better.
- If the opponent might skip a turn or is unsure, include <opponent_action>pass</opponent_action>.

Input format:
game_state: {game_state}
prior_actions: {prior_actions}
last_move_by_you: {last_move}

Output format:
<think> ...opponent reasoning... </think>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>
<opponent_action> ... </opponent_action>
"""