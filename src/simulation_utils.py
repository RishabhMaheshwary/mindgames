import re
import hashlib
from typing import List, Optional, Tuple, Dict
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor, as_completed
from prompts import *
import random
# Utility functions to extract actions from tags
def extract_tagged_items(text: str, tag: str) -> List[str]:
    pattern = f"<{tag}>(.*?)</{tag}>"
    return re.findall(pattern, text, flags=re.DOTALL)

def _truncate(s: str, max_chars: int = 160) -> str:
    s = s.strip()
    return s if len(s) <= max_chars else s[:max_chars-3] + "..."

def _show_branch(branch, max_steps: int = 4, max_chars: int = 160) -> str:
    """Readable one-liner: first K steps, each truncated."""
    steps = [ _truncate(x, max_chars=max_chars) for x in branch[:max_steps] ]
    tail = "" if len(branch) <= max_steps else f" ...(+{len(branch)-max_steps} steps)"
    return " | ".join(steps) + tail

def _print_candidates(header: str, candidates, max_steps=3, max_chars=120):
    print(header)
    for i, b in enumerate(candidates):
        print(f"  [{i+1:02d}] { _show_branch(b, max_steps=max_steps, max_chars=max_chars) }")


# simulation_utils.py (near other helpers)

def _dedup_keep_order(items):
    seen = set()
    out = []
    for x in items:
        xs = x.strip()
        if xs not in seen:
            seen.add(xs)
            out.append(xs)
    return out

def _prioritize_non_pass(actions, tag_name):
    # Put explicit 'pass' (exact or bracketed) to the end
    pass_like = []
    non_pass = []
    for a in actions:
        a_clean = a.strip().lower()
        is_pass = (a_clean == "pass") or (a_clean == f"<{tag_name}>pass</{tag_name}>") or ("pass" == a_clean)
        (pass_like if is_pass else non_pass).append(a)
    return non_pass + pass_like



def simulate_game_tree(
    model,
    game_state: str,
    prior_actions: List[str],
    current_role: str,
    depth: int,
    max_depth: int,
    game: str = "Colonel Blotto",
    k_per_node: int = 5,        # keep top-K proposals per node by prompt order
    debug: bool = False,
    debug_max_chars: int = 160,
) -> List[List[str]]:
    """
    Simple ToT with score-based beam pruning (fast). No pairwise inside.
    Pairwise should be used ONLY at the end on the final set of leaves.
    """
    
    if game == "colonel blotto":
        if current_role == "agent":
            prompt = COLONEL_BOLOTTO
        else:
            prompt = COLONEL_BOLOTTO_OPPONENT
    elif game == "3-player iterated prisoner's dilemma":
        if current_role == "agent":
            prompt = TPID
        else:
            prompt = TPID_OPPONENT
    elif game == "codenames":
        if current_role == "agent":
            prompt = CODENAMES
        else:
            prompt = CODENAMES_OPPONENT
    else:
        if current_role == "agent":
            prompt = NEXT_STEP_PROMPT_TEMPLATE
        else:
            prompt = OPPONENT_MOVE_PROMPT_TEMPLATE

    # Stop: closed leaf
    if depth >= max_depth:
        if debug:
            print(f"[ToT] Reached max_depth={max_depth}. Close leaf:")
            print(f"      {_show_branch(prior_actions, max_steps=8, max_chars=debug_max_chars)}")
        return [prior_actions[:]] if prior_actions else []

    # Propose
    prompt_formatted = prompt.format(
        game_state=game_state,
        prior_actions="\n".join(prior_actions) if prior_actions else "None",
        # last_move=prior_actions[-1] if prior_actions else "None"
    )
    messages = [
        {"role": "system", "content": "You are a clever player here to win the game."},
        {"role": "user", "content": prompt_formatted}
    ]
    tag = "action" if current_role == "agent" else "opponent_action"
    response = model.get_completion(messages)
    actions = extract_tagged_items(response, tag)

    if debug:
        print(f"[ToT][d={depth}] Role={current_role}; got {len(actions)} raw.")
        print(f"   Raw: {_truncate(response, debug_max_chars)}")

    # Dedup, push 'pass' last, slice top-K by prompt ordering
    actions = _dedup_keep_order(actions)
    actions = _prioritize_non_pass(actions, tag_name=tag)
    if k_per_node is not None and k_per_node > 0:
        actions = actions[:k_per_node]
    if not actions:
        actions = ["pass"]

    if debug:
        print(f"[ToT][d={depth}] Actions after hygiene (top {k_per_node}):")
        for i, a in enumerate(actions, 1):
            print(f"   - {i}. {_truncate(a, debug_max_chars)}")

    # Build candidate partial paths for this ply
    open_tag = f"<{tag}>"; close_tag = f"</{tag}>"
    candidate_paths = []
    for a in actions:
        a_stripped = a.strip()
        step = a_stripped if a_stripped.startswith(open_tag) else f"{open_tag}{a_stripped}{close_tag}"
        candidate_paths.append(prior_actions + [step])

    if debug:
        _print_candidates(f"[ToT][d={depth}] Candidates before beam:", candidate_paths,
                          max_steps=4, max_chars=debug_max_chars)

    # Recurse
    branches = []
    next_role = "opponent" if current_role == "agent" else "agent"
    for idx, new_prior in enumerate(candidate_paths, 1):
        if debug:
            print(f"[ToT][d={depth}] -> Recurse child {idx}/{len(candidate_paths)} ({current_role}→{next_role})")
            print(f"     {_show_branch(new_prior, max_steps=5, max_chars=debug_max_chars)}")
        sub = simulate_game_tree(
            model=model,
            game_state=game_state,
            prior_actions=new_prior,
            current_role=next_role,
            depth=depth + 1,
            max_depth=max_depth,
            k_per_node=k_per_node,
            game=game,
            debug=debug,
            debug_max_chars=debug_max_chars,
        )
        branches.extend(sub if sub else [new_prior])

    if debug and depth == 0:
        print(f"[ToT] Completed tree: leaves={len(branches)}")
        _print_candidates("[ToT] Leaf trajectories:", branches, max_steps=6, max_chars=debug_max_chars)

    return branches


def extract_chosen_index(text: str) -> Optional[int]:
    """
    Looks for a single <game_state index="i">…</game_state> in the evaluator’s output
    and returns i as int.
    """
    m = re.search(r'\[\[(\d+)\]\]', text)
    return int(m.group(1)) if m else None


def extract_pair_choice(text: str) -> Optional[int]:
    """
    Parses evaluator output to find [[1]] or [[2]] (numeric).
    Falls back to [[A]]/[[B]] if present. Returns 1 or 2, else None.
    """
    m = re.search(r'\[\[\s*([12])\s*\]\]', text)
    if m:
        return int(m.group(1))
    m = re.search(r'\[\[\s*([AaBb])\s*\]\]', text)
    if m:
        return 1 if m.group(1).lower() == "a" else 2
    return None

def _format_branch_for_prompt(branch: List[str]) -> str:
    """
    Convert a branch (list of tagged actions like <action>...</action> / <opponent_action>...</opponent_action>)
    into a readable block. We simply join them with newlines so the evaluator sees the sequence.
    """
    return "\n".join(branch)

def evaluate_best_branch(
    model,
    base_state: str,
    branches: List[List[str]],
    rounds_per_pair: int = 1,
    system_prompt: str = "You are a game evaluator.",
    debug: bool = False,
    debug_max_chars: int = 220,
    pairs={},
) -> str:
    if not branches:
        if debug: print("[Eval] No branches; returning 'pass'")
        return "pass"

    nonempty = [b for b in branches if len(b) > 0]
    if not nonempty:
        if debug: print("[Eval] Branches empty; returning 'pass'")
        return "pass"
    branches = nonempty

    n = len(branches)
    wins = [0.0] * n

    if debug:
        print(f"[Eval] Starting pairwise evaluation: {n} branches, {rounds_per_pair} round(s) per pair")
        _print_candidates("[Eval] Candidate branches:", branches, max_steps=5, max_chars=debug_max_chars)

    def evaluate_pair(i, j, existing_pairs):
        if (tuple(branches[i]), tuple(branches[j])) in existing_pairs:
            print(f"[Eval] Using cached pair: {i}, {j}")
            return i, j, existing_pairs[(tuple(branches[i]), tuple(branches[j]))]
        future_1 = "\n".join(branches[i])
        future_2 = "\n".join(branches[j]).replace("<action>", "<opponent_action>").replace("</action>", "</opponent_action>")
        votes_ij = [0, 0]
        for _ in range(rounds_per_pair):
            prompt = PAIRWISE_EVAL_PROMPT_TEMPLATE.format(
                base_state=base_state,
                future_1=future_1,
                future_2=future_2,
            )
            prompt_reverse = PAIRWISE_EVAL_PROMPT_TEMPLATE.format(
                base_state=base_state,
                future_1=future_2,
                future_2=future_1,
            )
            resp = model.get_completion([{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}])
            resp_reverse = model.get_completion([{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt_reverse}])
            choice = extract_pair_choice(resp)
            choice_reverse = extract_pair_choice(resp_reverse)
            if choice == 1 and choice_reverse == 2:
                votes_ij[0] += 1
                votes_ij[1] += -1
            elif choice == 2 and choice_reverse == 1:
                votes_ij[1] += 1
                votes_ij[0] += -1
            else:
                votes_ij[0] += 0.5
                votes_ij[1] += 0.5
        return i, j, votes_ij

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(evaluate_pair, i, j, pairs): (i, j) for i, j in combinations(range(n), 2)}
        for future in as_completed(futures):
            i, j, votes_ij = future.result()
            pairs[(tuple(branches[i]), tuple(branches[j]))] = votes_ij
            if votes_ij[0] > votes_ij[1]:
                wins[i] += 1
            elif votes_ij[1] > votes_ij[0]:
                wins[j] += 1
            else:
                wins[i] += 0.5
                wins[j] += 0.5

    total_wins = sum(wins)
    probabilities = [win / total_wins for win in wins]
    winner_idx = random.choices(range(n), weights=probabilities, k=1)[0]
    first = branches[winner_idx][0]
    action = first.replace("<action>", "").replace("</action>", "")

    if debug:
        print(f"[Eval] Final wins: {wins}")
        print(f"[Eval] Winner: Branch #{winner_idx+1}")
        print(f"[Eval] Selected FIRST ACTION: {action}")

    return action, pairs


def evaluate_best_branch_old(
    model,
    base_state: str,
    branches: List[List[str]],
    debug=True,          # <— turn on evaluator logs
    debug_max_chars=220,
    role="agent"
) -> List[str]:
    """
    Use the EVAL_PROMPT to pick the best of several simulated branches.

    Args:
        agent: your GPTMiniAgent
        base_state: the original game_state description
        branches: a list of branches, where each branch is a list of tagged actions

    Returns:
        The branch (list of actions) that the model judged best.
    """
    # Build the <futures> section: one block per branch
    futures = []
    for idx, branch in enumerate(branches):
        if len(branch) == 2 and role == "opponent":
            branch[0], branch[1] = branch[1], branch[0]
        branch = "\n".join(branch) 
        block = (
            f"<future_game_state index={idx+1}>\n{branch}\n</future_game_state>"
        )
        futures.append(block)
    futures_blocks = "\n\n".join(futures)

    prompt = EVAL_PROMPT_TEMPLATE.format(
        base_state=base_state,
        futures_blocks=futures_blocks
    )
    if debug:
        print("[Eval] Prompt:")
        print(prompt)
        
    messages = [
        {"role": "system", "content": "You are a game evaluator."},
        {"role": "user", "content": prompt}
    ]

    response = model.get_completion(messages)
    if debug:
        print("[Eval] Response:")
        print(response)
    chosen_idx = extract_chosen_index(response)
    if debug:
        print("[Eval] Chosen index:", chosen_idx)
    if chosen_idx and 1 <= chosen_idx <= len(branches):
        # if role == "agent":
        return branches[chosen_idx - 1][0].replace("<action>", "").replace("</action>", "")
        # else:
        #     return branches[chosen_idx - 1][-1].replace("<action>", "").replace("</action>", "")
    else:
        # fallback: pick first
        return branches[0][0].replace("<action>", "").replace("</action>", "")    