import discord
import asyncio
import json
from discord.ext import commands
import config
import re
import random
import datetime
import unicodedata
from flask import Flask
from threading import Thread
import os
import requests
import time
import math
import textwrap

# Preset named groups for convenience in commands like: !op true ultima
# Keys are lower-cased alias names; values are lists of exact song titles to expand.
PRESET_GROUPS = {
    'ultima': [
        'Change Our MIRAI！', 'Invitation', 'Teriqma', 'luna blu', 'MUSIC PЯAYER',
        'First Twinkle', 'Hyperion', '最愛テトラグラマトン', 'WE GOTTA SOUL', 'ハルシナイト'
    ]
}

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents, activity=discord.Game("!omi")) # botをプレイ中)
#intents = discord.Intents.all()
#client = discord.Client(command_prefix='!',intents=intents)

# Bot起動時に呼び出される関数
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # Set a concise presence that points users to the !op help text.
    # Keep the string short so it fits in the Discord status area.
    try:
        await bot.change_presence(activity=discord.Game("!omi • !op help"))
        print("Presence updated: !omi • !op help")
    except Exception as e:
        # Don't raise; presence update failure shouldn't stop the bot
        print(f"Failed to update presence: {e}")

@bot.command()
async def op(ctx, a: str = None, *names: str):
    """Over-power 集計処理。
    Two calling styles are supported:
      1) Bot command: !op <exclude_bool> <space-separated-names>
         - a: boolean-ish string (true/false). If true, songs in b will be excluded.
         - b: space-separated song names to exclude.
      2) Internal call from `omi`: op(ctx, json_data, op2)
         - a: json_data dict
         - b: op2 string (currently 'sum' or None)

    The aggregation rule: for ULT/MAS charts take (const+3)*5 as max OP and sum.
    If exclusion is enabled and a song name is in the exclude list:
      - If the encountered chart is MAS -> skip (do not count)
      - If the encountered chart is ULT -> try to use the MAS chart's OP instead (if exists)
    """
    # Detect internal call style: op(ctx, json_data, op2)
    if isinstance(a, dict):
        json_data = a
        # For internal calls, accept the first extra arg as the op mode (e.g. 'sum')
        op_mode = names[0] if len(names) >= 1 else 'sum'
        exclude_mode = False
        exclude_set = set()
    else:
        # Command-style: support either `!op true name1 name2` or `!op name1 name2`
        # Also support quoted multi-word song names using shlex parsing of the raw message.
        # Example: !op true "My Song" "Other Song"
        raw_args = None
        try:
            # ctx.message.content is like: '!op true "Song Name" Another'
            parts = ctx.message.content.split(maxsplit=1)
            raw_args = parts[1] if len(parts) > 1 else ''
        except Exception:
            raw_args = ''
        parsed_args = []
        if raw_args:
            import shlex
            try:
                parsed_args = shlex.split(raw_args)
            except Exception:
                # fallback to simple split if shlex fails
                parsed_args = raw_args.split()
        

    # Now parsed_args[0] corresponds to what was passed as `a` and the rest as names
    json_data = None
    op2 = None
    exclude_mode = False
    exclude_set = set()
    op_mode = None
    # percent parameters (optional): user may include 'pct' or '--pct' or 'percent' followed by two floats
    percent_start = None
    percent_target = None
    # optional override for representative const
    rep_const_override = None
    # derive flags and names from parsed_args (safer for quoted names)
    if parsed_args:
        first = parsed_args[0]
        rest = parsed_args[1:]
        # detect and extract percent flags and rep-const overrides from parsed_args (they may appear anywhere)
        cleaned = []
        i = 0
        # ensure aj_max_const and assign bounds exist in scope even if not provided
        aj_max_const = None
        assign_min_const = None
        assign_max_const = None
        tokens = [t for t in parsed_args]
        while i < len(tokens):
            tk = tokens[i]
            low = str(tk).lower()
            if low in ('pct'):
                # attempt to read two following numeric tokens
                try:
                    s = float(tokens[i+1])
                    t = float(tokens[i+2])
                    percent_start = s
                    percent_target = t
                    i += 3
                    continue
                except Exception:
                    cleaned.append(tk)
                    i += 1
                    continue
            # rep-const removed; use assign-min/max to derive representative const instead
            elif low in ('ajmax'):
                try:
                    ajm = float(tokens[i+1])
                    # aj_max_const: user-specified maximum chart const for AJ suggestions
                    aj_max_const = ajm
                    i += 2
                    continue
                except Exception:
                    cleaned.append(tk)
                    i += 1
                    continue
            elif low in ('minconst'):
                try:
                    am = float(tokens[i+1])
                    assign_min_const = am
                    i += 2
                    continue
                except Exception:
                    cleaned.append(tk)
                    i += 1
                    continue
            elif low in ('maxconst'):
                try:
                    aM = float(tokens[i+1])
                    assign_max_const = aM
                    i += 2
                    continue
                except Exception:
                    cleaned.append(tk)
                    i += 1
                    continue
            else:
                cleaned.append(tk)
                i += 1

        # rebuild first/rest from cleaned tokens
        if cleaned:
            first = cleaned[0]
            rest = cleaned[1:]
        else:
            first = None
            rest = []

        # determine op_mode from the first token (if present)
        if first is not None:
            lf = str(first).lower()
            if lf == 'help':
                op_mode = 'help'
            elif lf == 'cal':
                op_mode = 'cal'
            elif lf == 'true':
                op_mode = 'true'
            elif lf == 'false':
                op_mode = 'false'
            elif lf == 'suggest':
                op_mode = 'suggest'
            else:
                op_mode = 'sum'

        # set exclude_set based on op_mode and tokens
        # build the exclude_set / name list by expanding any preset keys
        if op_mode == 'true':
            exclude_mode = True
            raw_tokens = [n.strip() for n in rest if n and n.strip()]
        else:
            exclude_mode = False
            all_names = ([first] if first is not None else []) + rest
            raw_tokens = [n.strip() for n in all_names if n and n.strip()]

        expanded = []
        for tok in raw_tokens:
            key = tok.lower()
            if key in PRESET_GROUPS:
                expanded.extend(PRESET_GROUPS[key])
            else:
                expanded.append(tok)
        exclude_set = set(expanded)
    else:
        # no args provided
        exclude_set = set()

    # Decide top-level op mode: help / cal / true (exclude) / sum (default)
    op_mode = 'sum'
    # help explicit
    if 'first' in locals() and first is not None and str(first).lower() == 'help':
        op_mode = 'help'
    # cal explicit
    elif ('first' in locals() and first is not None and str(first).lower() == 'cal') or (isinstance(a, str) and str(a).lower() == 'cal'):
        op_mode = 'cal'
    # true/exclude mode explicit
    elif 'first' in locals() and first is not None and str(first).lower() == 'true':
        op_mode = 'true'
    elif 'first' in locals() and first is not None and str(first).lower() == 'false':
        op_mode = 'false'
    elif 'first' in locals() and first is not None and str(first).lower() == 'suggest':
        op_mode = 'suggest'
    # if invoked internally with op2, prefer that
    # note: internal-call op_mode already set when a is dict; no additional op2 handling required

    # Handle help quickly
    if op_mode == 'help':
        help_text = textwrap.dedent("""\
        !op のヘルプ: 使用可能なオプションと補助コマンド一覧:
        使い方（基本）: !op [sum|true|cal|suggest|help] [options]

        - sum:
        合計オーバーパワー(Max)を計算表示します（デフォルトモード）

        - true:
        除外モード（例: !op true "songA" "songB"）
        オプション（trueでもfalseでも利用可能）:
            pct <start> <target>        : パーセント差分の計算
            ajmax <const>               : AJ 候補定数上限
            minconst <const>            : 割当定数下限
            maxconst <const>            : 割当定数上限
        例1: !op true ultima "SongA" "SongB" pct 99.0 99.01 minconst 12.0 maxconst 13.5 ajmax 13.2
        例2: !op false pct 99.0 99.01 minconst 12.0 maxconst 13.5 ajmax 13.2

        - cal:
        MY_OP を MAX_OP に対する%で表示します(小数点以下5ケタ)
        使い方: !op cal <MAX_OP> <MY_OP>

        - suggest:
        入力文字列から曲名候補を表示します
        使い方: !op suggest <partial>

        - help:
        このヘルプを表示します

        その他: 複数ワードの曲名はダブルクォートで囲んでください。
        """)
        await ctx.send(help_text)
        return

    # Quick-calculation mode: support `!op cal <MAX_OP> <MY_OP>` to show MY_OP as percent of MAX_OP
    if op_mode == 'cal':
        try:
            cal_vals = None
            if 'first' in locals() and first is not None and str(first).lower() == 'cal':
                cal_vals = rest
            elif isinstance(a, str) and str(a).lower() == 'cal':
                cal_vals = list(names)

            if not cal_vals or len(cal_vals) < 2:
                await ctx.send("使い方: !op cal <MAX_OP> <MY_OP> （数値を2つ指定してください）")
                return
            try:
                max_op_val = float(cal_vals[0])
                my_op_val = float(cal_vals[1])
            except Exception:
                await ctx.send("MAX_OP と MY_OP は数値で指定してください。例: `!op cal 12000 3456`")
                return

            if max_op_val == 0:
                pct = 0.0
            else:
                pct = (my_op_val / max_op_val) * 100.0

            await ctx.send(f"割合: {pct:.5f}% (MY OP: {my_op_val:.2f} / MAX OP: {max_op_val:.2f})")
            return
        except Exception:
            # fall through to normal behavior
            return

    # Load json if not provided
    if json_data is None:
        try:
            with open("data_c.json", 'r') as f:
                json_data = json.load(f)
        except Exception as e:
            await ctx.send(f"データ読み込みエラー: {e}")
            return

    # extract aggregation into helper to simplify op function
    def select_entries(data, exclude_set, exclude_mode):
        name_map = {}
        entries = []
        mas_count = 0
        ult_count = 0
        for v in data.values():
            try:
                chart_const = float(v['data'][2])
            except Exception:
                continue
            chart_type = v['data'][0]
            if chart_type in ("ULT", "MAS"):
                if chart_type == 'MAS':
                    mas_count += 1
                elif chart_type == 'ULT':
                    ult_count += 1
                name = v['name']
                name_map.setdefault(name, []).append((chart_type, chart_const, v.get('diff', '')))
                entries.append((name, chart_const, v.get('diff', ''), chart_type, v['data'][1]))

        entries.sort(key=lambda x: x[1], reverse=True)

        # selection
        selected_entries = {}
        total_op = 0.0
        processed_mas_selected = 0
        processed_ult_selected = 0
        mas_selected_counts = {}

        for name, const, diffv, chart_type, genre in entries:
            if exclude_mode and name in exclude_set:
                if chart_type == 'ULT':
                    mas_entries = [t for t in name_map.get(name, []) if t[0] == 'MAS']
                    if mas_entries:
                        mas_const = mas_entries[0][1]
                        max_op = (mas_const + 3) * 5
                        sel_line = f"Title: {name}\tDiff:MAS\tType:MAS\tConst:{mas_const}\tMaxOP:{max_op:.2f}"
                        if name in selected_entries:
                            continue
                        selected_entries[name] = ('MAS', max_op, sel_line, mas_const, 'MAS')
                        total_op += max_op
                        processed_mas_selected += 1
                        mas_selected_counts[name] = mas_selected_counts.get(name, 0) + 1
                    else:
                        continue
                else:
                    continue
            else:
                max_op = (const + 3) * 5
                sel_line = f"Title: {name}\tDiff:{diffv}\tType:{chart_type}\tConst:{const}\tMaxOP:{max_op:.2f}"
                if name not in selected_entries:
                    selected_entries[name] = (chart_type, max_op, sel_line, const, diffv)
                    total_op += max_op
                    if chart_type == 'MAS':
                        processed_mas_selected += 1
                        mas_selected_counts[name] = mas_selected_counts.get(name, 0) + 1
                    elif chart_type == 'ULT':
                        processed_ult_selected += 1
                else:
                    existing_type, existing_op, existing_line, existing_const, existing_diff = selected_entries[name]
                    if existing_type == 'MAS' and chart_type == 'ULT':
                        total_op -= existing_op
                        processed_mas_selected -= 1
                        mas_selected_counts[name] = mas_selected_counts.get(name, 1) - 1
                        if mas_selected_counts.get(name, 0) <= 0:
                            mas_selected_counts.pop(name, None)
                        selected_entries[name] = (chart_type, max_op, sel_line, const, diffv)
                        total_op += max_op
                        processed_ult_selected += 1
                    else:
                        continue

        selected_list = sorted(selected_entries.items(), key=lambda kv: kv[1][1], reverse=True)
        selected_lines = [v[2] for k, v in selected_list]
        mas_song_names = set([k for k, v in name_map.items() if any(t[0] == 'MAS' for t in v)])
        total_charts = mas_count + ult_count
        return selected_entries, total_op, selected_lines, processed_mas_selected, processed_ult_selected, mas_song_names, entries, mas_count, ult_count, total_charts

    def calculate_total_op(json_data, exclude_set, exclude_mode):
        """
        Calculate and return the full select_entries outputs so callers can use them.
        Returns the exact tuple from select_entries.
        """
        return select_entries(json_data, exclude_set, exclude_mode)

    def generate_suggestions(selected_entries, entries, total_op, percent_start, percent_target, aj_max_const, assign_min_const, assign_max_const):
        """
        Generate human-friendly suggestion messages based on a desired percent delta.
        This helper is intentionally conservative and works the same whether exclude_mode
        is True or False as long as the caller provides the selected_entries and entries
        computed for the current exclude_set/exclude_mode.

        Returns: list of message strings to send (may be empty).
        """
        msgs = []
        try:
            def to_frac(x: float) -> float:
                try:
                    xv = float(x)
                except Exception:
                    return 0.0
                if xv > 1.0:
                    return xv / 100.0
                return xv

            # Choose representative const according to assign_min_const/maxconst rules:
            # - If both min and max provided: use their average.
            # - If only one provided: use that one.
            # - If neither provided: return an error message and exit early.
            if assign_min_const is None and assign_max_const is None:
                msgs.append("エラー: 提案を行うために 'minconst' または 'maxconst' のいずれかを指定してください。例: minconst 12.0 maxconst 13.5")
                return msgs

            if assign_min_const is not None and assign_max_const is not None:
                rep_const = (assign_min_const + assign_max_const) / 2.0
            elif assign_min_const is not None:
                rep_const = assign_min_const
            else:
                rep_const = assign_max_const

            # Simple action-effect model (same as original rules):
            # AJ (with implied FC) ~= +1.0 OP
            # FC ~= +0.5 OP
            # AJC ~= +0.25 OP
            # score-step (approx): 500 points ~= +0.75 OP (approximation used previously)
            aj_op = 1.0
            fc_op = 0.5
            ajc_op = 0.25
            score_step_points = 500
            score_step_op = 0.75

            needed_pos = None if needed is None else (needed if needed > 0 else 0.0)

            # Minimal single-action suggestions
            aj_only = None
            fc_only = None
            ajc_only = None
            score_only_steps = None
            if needed_pos is not None:
                aj_only = math.ceil(needed_pos / aj_op) if aj_op > 0 else None
                fc_only = math.ceil(needed_pos / fc_op) if fc_op > 0 else None
                ajc_only = math.ceil(needed_pos / ajc_op) if ajc_op > 0 else None
                score_only_steps = math.ceil(needed_pos / score_step_op) if score_step_op > 0 else None

                msgs.append("----- 単一手段での概算提案 (必要量の最小整数) -----")
                if aj_only is not None:
                    msgs.append(f"AJのみ: {aj_only} 回 (想定増分: {aj_only*aj_op:.2f} OP)")
                if fc_only is not None:
                    msgs.append(f"FCのみ: {fc_only} 回 (想定増分: {fc_only*fc_op:.2f} OP)")
                if ajc_only is not None:
                    msgs.append(f"AJCのみ: {ajc_only} 回 (想定増分: {ajc_only*ajc_op:.2f} OP)")
                if score_only_steps is not None:
                    msgs.append(f"スコア増加(+500基準)のみ: {score_only_steps} ステップ ({score_only_steps*score_step_points} pts, 想定増分: {score_only_steps*score_step_op:.2f} OP)")
            else:
                msgs.append("----- パーセント指定がありません: サンプル増分 (1〜5回) を表示します -----")
                for n in range(1, 6):
                    msgs.append(f"AJ x{n}: 想定増分 {n*aj_op:.2f} OP | FC x{n}: {n*fc_op:.2f} OP | AJC x{n}: {n*ajc_op:.2f} OP | スコアステップ x{n}: {n*score_step_op:.2f} OP ({n*score_step_points} pts)")

            # Build candidate pool filtered by assign_min_const / assign_max_const for assignment suggestions
            pool_titles_all = []
            try:
                for name, v in selected_entries.items():
                    try:
                        c = v[3]
                    except Exception:
                        continue
                    if not isinstance(c, (int, float)):
                        continue
                    if assign_min_const is not None and c < assign_min_const:
                        continue
                    if assign_max_const is not None and c > assign_max_const:
                        continue
                    pool_titles_all.append((name, c))
                # sort by const desc as a default ordering
                pool_titles_all.sort(key=lambda x: x[1], reverse=True)
            except Exception:
                pool_titles_all = []

            pool_names = [t[0] for t in pool_titles_all]

            def sample_titles(n, avoid=None):
                if not pool_names or n <= 0:
                    return []
                candidates = pool_names if avoid is None else [p for p in pool_names if p not in avoid]
                if not candidates:
                    # fallback to full pool with replacement
                    return [random.choice(pool_names) for _ in range(n)]
                if n <= len(candidates):
                    return random.sample(candidates, n)
                # if n > available, sample all then fill with replacement
                res = candidates.copy()
                while len(res) < n:
                    res.append(random.choice(candidates))
                return res

            # Mixed-plan optimization: search for integer counts of AJ, AJC, FC, score-step
            # that reach needed_pos with minimal weighted cost.
            # Default action gains (OP) are defined above: aj_op, ajc_op, fc_op, score_step_op
            # Weights represent difficulty/cost from player's perspective (higher = more costly):
            if rep_const <= 14.5:
                w_aj = 0.8
                w_ajc = 0.2
                w_fc = 1.0
                w_score = 2.0
            else:
                w_aj = 1.5
                w_ajc = 2.2
                w_fc = 1.0
                w_score = 2.0

            best_plan = None
            best_cost = float('inf')
            best_gain = 0.0
            feasible_plans = []  # list of (cost, gain, (aj,ajc,fc,score))

            if needed_pos is not None and needed_pos > 0:
                # Compute reasonable caps per action to limit search space
                # Allow a small buffer (+3) beyond theoretical minimum
                aj_cap = min(20, int(math.ceil(needed_pos / aj_op)) + 3)
                ajc_cap = min(20, int(math.ceil(needed_pos / ajc_op)) + 3)
                fc_cap = min(40, int(math.ceil(needed_pos / fc_op)) + 3)
                score_cap = min(40, int(math.ceil(needed_pos / score_step_op)) + 3)

                # Brute-force search (bounded). Keep loops ordered by expected cost to improve early pruning.
                for aj_count in range(0, aj_cap + 1):
                    aj_gain = aj_count * aj_op
                    aj_cost = aj_count * w_aj
                    if aj_gain >= needed_pos:
                        total_cost = aj_cost
                        if total_cost < best_cost:
                            best_cost = total_cost
                            best_plan = (aj_count, 0, 0, 0)
                            best_gain = aj_gain
                        continue
                    # small pruning: if even without other actions aj_cost already >= best_cost, skip
                    if aj_cost >= best_cost:
                        continue
                    for ajc_count in range(0, ajc_cap + 1):
                        ajc_gain = ajc_count * ajc_op
                        ajc_cost = ajc_count * w_ajc
                        gain_aj_ajc = aj_gain + ajc_gain
                        cost_aj_ajc = aj_cost + ajc_cost
                        if gain_aj_ajc >= needed_pos:
                            if cost_aj_ajc < best_cost:
                                best_cost = cost_aj_ajc
                                best_plan = (aj_count, ajc_count, 0, 0)
                                best_gain = gain_aj_ajc
                            continue
                        if cost_aj_ajc >= best_cost:
                            continue
                        for fc_count in range(0, fc_cap + 1):
                            fc_gain = fc_count * fc_op
                            fc_cost = fc_count * w_fc
                            gain_aj_ajc_fc = gain_aj_ajc + fc_gain
                            cost_aj_ajc_fc = cost_aj_ajc + fc_cost
                            if gain_aj_ajc_fc >= needed_pos:
                                if cost_aj_ajc_fc < best_cost:
                                    best_cost = cost_aj_ajc_fc
                                    best_plan = (aj_count, ajc_count, fc_count, 0)
                                    best_gain = gain_aj_ajc_fc
                                continue
                            if cost_aj_ajc_fc >= best_cost:
                                continue
                            # compute remaining needed and minimal number of score steps to cover it
                            rem_needed = needed_pos - gain_aj_ajc_fc
                            # estimate minimal score steps and search around it rather than full loop
                            min_score_needed = int(math.ceil(rem_needed / score_step_op))
                            for score_count in range(0, min(score_cap, min_score_needed + 3) + 1):
                                score_gain = score_count * score_step_op
                                total_gain = gain_aj_ajc_fc + score_gain
                                if total_gain < needed_pos:
                                    continue
                                score_cost = score_count * w_score
                                total_cost = cost_aj_ajc_fc + score_cost
                                if total_cost < best_cost - 1e-9:
                                    best_cost = total_cost
                                    best_plan = (aj_count, ajc_count, fc_count, score_count)
                                    best_gain = total_gain
                                # record feasible plan
                                feasible_plans.append((total_cost, total_gain, (aj_count, ajc_count, fc_count, score_count)))

                # If we found plans, sort and present several alternatives
                if feasible_plans:
                    feasible_plans.sort(key=lambda x: (x[0], -x[1]))
                    # dedupe by (aj,ajc,fc,score) keeping best cost
                    seen_plans = {}
                    for cost, gain, tpl in feasible_plans:
                        if tpl not in seen_plans or cost < seen_plans[tpl][0]:
                            seen_plans[tpl] = (cost, gain)
                    unique_plans = sorted([(c,g,t) for t,(c,g) in seen_plans.items()], key=lambda x: (x[0], -x[1]))

                    msgs.append("----- 混合プラン候補（重み付き評価、上位3） -----")
                    msgs.append(f"代表定数 (rep_const): {rep_const:.2f}")
                    # present up to 3 strategies: min-cost, AJ-priority, FC-priority/score-priority, then balanced
                    presented = 0
                    # helper to build per-action candidate lists for a given plan tpl
                    def build_action_candidates(plan_tpl):
                        aj_n, ajc_n, fc_n, sc_n = plan_tpl
                        selected = set()
                        lines = []

                        # prepare a quick map from title -> const for display
                        pool_const_map = {t[0]: t[1] for t in pool_titles_all}

                        def fmt_titles(lst):
                            # format as: Title (const)
                            out = []
                            for t in lst:
                                c = pool_const_map.get(t)
                                if c is None:
                                    out.append(f"{t}")
                                else:
                                    out.append(f"{t} ({c})")
                            return out

                        # AJC: pick from pool sorted by const ascending (starting from minconst)
                        asc_sorted = sorted(pool_titles_all, key=lambda x: x[1])
                        ajc_candidates = [n for n, c in asc_sorted]
                        if ajc_n > 0:
                            if len(ajc_candidates) >= ajc_n:
                                ajc_sel = ajc_candidates[:ajc_n]
                            else:
                                ajc_sel = ajc_candidates + [p for p in sample_titles(ajc_n - len(ajc_candidates))]
                        else:
                            ajc_sel = []
                        for s in ajc_sel:
                            selected.add(s)

                        # AJ: select from pool filtered by assign_min_const .. aj_max_const (if aj_max_const is set)
                        aj_sel = []
                        if aj_n > 0:
                            # build AJ-specific candidate list honoring aj_max_const and assign_min_const
                            if aj_max_const is not None or assign_min_const is not None:
                                aj_candidates = []
                                for tname, tconst in pool_titles_all:
                                    if assign_min_const is not None and tconst < assign_min_const:
                                        continue
                                    if aj_max_const is not None and tconst > aj_max_const:
                                        continue
                                    aj_candidates.append(tname)
                                # if not enough AJ candidates, fall back to sampling from full pool (excluding selected)
                                if len(aj_candidates) >= aj_n:
                                    # sample without replacement from aj_candidates
                                    aj_sel = random.sample(aj_candidates, aj_n)
                                elif aj_candidates:
                                    # take all then fill with samples from remaining pool
                                    aj_sel = aj_candidates.copy()
                                    need = aj_n - len(aj_sel)
                                    # choose from pool_names excluding already selected/aj_sel
                                    extras = [p for p in pool_names if p not in selected and p not in aj_sel]
                                    while need > 0 and extras:
                                        pick = random.choice(extras)
                                        aj_sel.append(pick)
                                        extras.remove(pick)
                                        need -= 1
                                    # if still need, allow replacement from full pool
                                    while len(aj_sel) < aj_n:
                                        aj_sel.append(random.choice(pool_names))
                                else:
                                    # no candidates matching constraints -> fallback to sample_titles
                                    aj_sel = sample_titles(aj_n, avoid=selected)
                            else:
                                # no AJ const bounds provided: use existing behavior
                                aj_sel = sample_titles(aj_n, avoid=selected)
                        else:
                            aj_sel = []
                        for s in aj_sel:
                            selected.add(s)

                        # FC: random from pool excluding selected
                        fc_sel = sample_titles(fc_n, avoid=selected) if fc_n > 0 else []
                        for s in fc_sel:
                            selected.add(s)

                        # Score: random from remaining pool (allow reuse if needed)
                        score_sel = sample_titles(sc_n, avoid=selected) if sc_n > 0 else []

                        if aj_sel:
                            lines.append("### AJ候補曲：\n\t" + "\n\t".join(fmt_titles(aj_sel)))
                        if ajc_sel:
                            # show AJC candidates in ascending-const order
                            lines.append("### AJC候補曲：\n\t" + "\n\t".join(fmt_titles(ajc_sel)))
                        if fc_sel:
                            lines.append("### FC候補曲：\n\t" + "\n\t".join(fmt_titles(fc_sel)))
                        if score_sel:
                            lines.append("### スコア増加候補曲：\n\t" + "\n\t".join(fmt_titles(score_sel)))
                        return lines

                    # 1) min-cost
                    uc = unique_plans[0]
                    msgs.append(f"## - [1] 最小コスト案:\n ```\n AJ:{uc[2][0]}回\n AJC:{uc[2][1]}回\n FC:{uc[2][2]}回\n Score:{uc[2][3]}回\n -> 増分 {uc[1]:.2f} OP, コスト {uc[0]:.2f}```")
                    try:
                        msgs.extend(build_action_candidates(uc[2]))
                    except Exception:
                        pass
                    presented += 1

                    # 2) AJ-priority: pick plan with largest AJ among feasible but cost within 120% of min-cost
                    min_cost = uc[0]
                    aj_pref = None
                    for c,g,t in unique_plans:
                        if c <= min_cost * 1.20:
                            if aj_pref is None or t[0] > aj_pref[2][0] or (t[0] == aj_pref[2][0] and c < aj_pref[0]):
                                aj_pref = (c,g,t)
                    if aj_pref and aj_pref[2] != uc[2]:
                        msgs.append(f"## - [2] AJ優先案:\n ```\n AJ:{aj_pref[2][0]}回\n AJC:{aj_pref[2][1]}回\n FC:{aj_pref[2][2]}回\n Score:{aj_pref[2][3]}回\n -> 増分 {aj_pref[1]:.2f} OP, コスト {aj_pref[0]:.2f}```")
                        try:
                            msgs.extend(build_action_candidates(aj_pref[2]))
                        except Exception:
                            pass
                        presented += 1

                    # 3) FC/Score-priority: prefer plan with highest (FC* w_fc + Score * w_score) within cost window
                    fc_pref = None
                    best_metric = -1
                    for c,g,t in unique_plans:
                        if c <= min_cost * 1.40:
                            metric = t[2] * w_fc + t[3] * w_score
                            if metric > best_metric:
                                best_metric = metric
                                fc_pref = (c,g,t)
                    if fc_pref and fc_pref[2] != uc[2] and (aj_pref is None or fc_pref[2] != aj_pref[2]):
                        msgs.append(f"## - [3] FC/Score優先案:\n ```\n AJ:{fc_pref[2][0]}回\n AJC:{fc_pref[2][1]}回\n FC:{fc_pref[2][2]}回\n Score:{fc_pref[2][3]}回\n -> 増分 {fc_pref[1]:.2f} OP, コスト {fc_pref[0]:.2f}```")
                        try:
                            msgs.extend(build_action_candidates(fc_pref[2]))
                        except Exception:
                            pass
                        presented += 1

                    # If fewer than 3 presented, add next best unique plans
                    idx = 1
                    while presented < 3 and idx < len(unique_plans):
                        c,g,t = unique_plans[idx]
                        msgs.append(f"## - [4] 代替案{presented+1}:\n ```\n AJ:{t[0]}回\n AJC:{t[1]}回\n FC:{t[2]}回\n Score:{t[3]}回\n -> 増分 {g:.2f} OP, コスト {c:.2f}```")
                        try:
                            msgs.extend(build_action_candidates(t))
                        except Exception:
                            pass
                        presented += 1
                        idx += 1
                else:
                    msgs.append("----- 混合案の最適化で候補が見つかりませんでした（検索範囲を広げる必要があります） -----")
            else:
                # no needed_pos (percent not specified) -> skip optimization
                pass
        except Exception:
            pass
        return msgs

    # simple sum-only mode: compute and report total OP
    if op_mode == 'sum':
        selected_entries, total_op, selected_lines, processed_mas_selected, processed_ult_selected, mas_song_names, entries, mas_count, ult_count, total_charts = calculate_total_op(json_data, exclude_set, exclude_mode)
        try:
            await ctx.send(f"チャート集計(合計チャート数): MAS: {mas_count} 曲, ULT: {ult_count} 曲, 合計: {total_charts} チャート\n計算対象曲数: {len(selected_lines)} 合計オーバーパワー(Max): {total_op:.2f}\n 処理されたMAS曲数(選定): {processed_mas_selected} 曲, 処理されたULT曲数(選定): {processed_ult_selected} 曲")
        except Exception:
            await ctx.send(f"計算対象曲数: {len(selected_lines)} 合計オーバーパワー(Max): {total_op:.2f}\nチャート集計(合計チャート数): MAS: {mas_count} 曲, ULT: {ult_count} 曲, 合計: {total_charts} チャート")
        return
    # suggest mode integrated into op: same behavior as !op_suggest
    elif op_mode == 'suggest':
        # build the partial query from remaining tokens
        # prefer cleaned/rest if available, fall back to names
        qtok = None
        try:
            if 'rest' in locals() and rest:
                qtok = " ".join(rest).strip()
            elif 'names' in locals() and names:
                qtok = " ".join(names).strip()
        except Exception:
            qtok = None

        if not qtok:
            await ctx.send("使い方: `!op suggest <部分文字列>` — 少なくとも1文字以上入力してください。")
            return

        q = qtok.strip().lower()

        # load data
        try:
            with open("data_c.json", 'r') as f:
                j = json.load(f)
        except Exception:
            await ctx.send("データ読み込みに失敗しました。`)")
            return

        # collect song title candidates
        titles = []
        for v in j.values():
            try:
                name = v.get('name', '')
                if name and q in name.lower():
                    titles.append(name)
            except Exception:
                continue

        # collect preset keys that match
        presets = [k for k in PRESET_GROUPS.keys() if q in k.lower()]

        # dedupe while preserving order
        seen = set()
        results = []
        for t in presets + titles:
            if t not in seen:
                seen.add(t)
                results.append(t)
            if len(results) >= 25:
                break

        if not results:
            await ctx.send("候補が見つかりませんでした。別の文字列でお試しください。")
        else:
            await ctx.send("候補 (最大25件):\n" + "\n".join(results))
        return
    # Update the 'true' mode to use the new function
    elif op_mode == 'true' or op_mode == 'false':
        selected_entries, total_op, selected_lines, processed_mas_selected, processed_ult_selected, mas_song_names, entries, mas_count, ult_count, total_charts = calculate_total_op(json_data, exclude_set, exclude_mode)
        msgs = []
        msgs2 = []
        base_flag_msgs = False
        base_sent_msgs2 = False
        try:
            msgs.append(f"チャート集計(合計チャート数): MAS: {mas_count} 曲, ULT: {ult_count} 曲, 合計: {total_charts} チャート")
            msgs2.append(f"チャート集計(合計チャート数): MAS: {mas_count} 曲, ULT: {ult_count} 曲, 合計: {total_charts} チャート")

            # If exclude_mode with an exclude_set (e.g., !op true ultima), compute a strict
            # exclusion total that completely removes those titles (no ULT->MAS substitution).
            if percent_start is None and percent_target is None:
                try:
                    def sum_op_excluding_entries(entries_list, excluded_titles):
                        """
                        Compute total OP using the same selection and exclusion rules as select_entries.
                        Behavior:
                          - Iterate charts sorted by const desc and select one chart per title.
                          - If a title is not excluded: pick the first-seen chart (highest const by sort),
                            but if later an ULT is seen and a MAS was selected, prefer the ULT (replace).
                          - If a title is excluded: skip MAS charts; if encountering an ULT for that title,
                            try to substitute the first MAS entry from the original name_map (if any).
                        This mirrors the logic in select_entries so the "一部除外" total matches other outputs.
                        """
                        # reconstruct name_map and entries (preserve original append order for name_map)
                        name_map = {}
                        entries = []
                        for name, const, diffv, chart_type, genre in entries_list:
                            name_map.setdefault(name, []).append((chart_type, const, diffv))
                            entries.append((name, const, diffv, chart_type, genre))

                        # sort by const desc to mirror select_entries
                        entries.sort(key=lambda x: x[1], reverse=True)

                        selected = {}
                        total = 0.0

                        for name, const, diffv, chart_type, genre in entries:
                            # already selected this title
                            if name in selected:
                                # allow replacement: if previously selected was MAS and now we see ULT, replace
                                existing_type, existing_op, existing_const = selected[name]
                                if existing_type == 'MAS' and chart_type == 'ULT':
                                    total -= existing_op
                                    max_op = (const + 3) * 5
                                    selected[name] = ('ULT', max_op, const)
                                    total += max_op
                                continue

                            if name in excluded_titles:
                                # exclusion behavior: skip MAS charts entirely; if ULT encountered, try to use
                                # an existing MAS entry (from name_map) instead
                                if chart_type == 'ULT':
                                    mas_entries = [t for t in name_map.get(name, []) if t[0] == 'MAS']
                                    if mas_entries:
                                        # use the first MAS entry (preserve original ordering behavior)
                                        mas_const = mas_entries[0][1]
                                        max_op = (mas_const + 3) * 5
                                        selected[name] = ('MAS', max_op, mas_const)
                                        total += max_op
                                    else:
                                        # no MAS to fall back to: skip this title entirely
                                        continue
                                else:
                                    # MAS chart and excluded -> skip
                                    continue
                            else:
                                # not excluded: select this chart
                                max_op = (const + 3) * 5
                                selected[name] = (chart_type, max_op, const)
                                total += max_op

                        return total

                    excluded_total = sum_op_excluding_entries(entries, exclude_set)
                    msgs2.append(f"計算対象曲数: {len(selected_lines)} 合計オーバーパワー(一部除外): {excluded_total:.2f}")
                except Exception:
                    # if anything fails, ignore the excluded total
                    pass
            else:
                msgs.append(f"計算対象曲数: {len(selected_lines)} 合計オーバーパワー(Max): {total_op:.2f}")
            msgs.append(f"処理されたMAS曲数(選定): {processed_mas_selected} 曲, 処理されたULT曲数(選定): {processed_ult_selected} 曲")
            msgs2.append(f"処理されたMAS曲数(選定): {processed_mas_selected} 曲, 処理されたULT曲数(選定): {processed_ult_selected} 曲")
        except Exception:
            pass

        # Send the base summary immediately so '!op true ...' prints processed counts even
        # when pct flags are not present. If pct flags are present, the pct branch will
        # append additional info and re-send a combined message.
        try:
            # send base summary now
            try:
                # If we computed a strict-exclusion summary (msgs2) and there are no pct flags,
                # prefer sending msgs2. Otherwise send msgs. Only send one of them to avoid
                # duplicate base summaries.
                if percent_start is None or percent_target is None:
                    await ctx.send("\n".join(msgs2))
                    base_sent_msgs2 = True
                else:
                    pass
            except Exception:
                pass

            # パーセント指定がある場合、必要なOP差分を計算して表示する
            if percent_start is not None and percent_target is not None:
                # accept percent as either 0-1 or 0-100; normalize to fraction
                def to_frac(x: float) -> float:
                    if x > 1.0:
                        return x / 100.0
                    return x

                ps = to_frac(percent_start)
                pt = to_frac(percent_target)
                if total_op <= 0:
                    await ctx.send("合計OPが0のためパーセント計算はできません。")
                else:
                    # current total_op corresponds to 100% of current sum; user wants to know
                    # how much OP is needed so that OP becomes target% of (total_op + added)
                    # Solve for added: (total_op + added) * pt = total_op + added_needed_from_some_source?
                    # Interpreting requirement: compute delta OP such that (total_op + delta) / total_op >= pt/ps ?
                    # Simpler and practical: compute OP needed to reach target% of the current maximum OP value.
                    # We'll compute required absolute OP to reach pt of (total_op) and report the difference from the value at ps.
                    current_value = total_op * ps
                    target_value = total_op * pt
                    needed = target_value - current_value
                    msgs.append(f"百分率指定: {percent_start} -> {percent_target} ({ps*100:.5f}% -> {pt*100:.2f}%)。現在のOP値: {current_value:.2f}、目標値: {target_value:.2f}、必要なOP差: {needed:.2f}")
                    if not base_sent_msgs2:
                        base_flag_msgs = True
        except Exception:
            pass

        # 追加提案: 必要OP差からユーザーが増やすべきFC/AJ/AJC数やスコア差を提案する
        try:
            if percent_start is not None and percent_target is not None:
                suggestion_msgs = generate_suggestions(selected_entries, entries, total_op, percent_start, percent_target, aj_max_const, assign_min_const, assign_max_const)
                if suggestion_msgs:
                    if base_flag_msgs:
                        await ctx.send("\n".join(msgs))
                        await ctx.send("\n".join(suggestion_msgs))
                else:
                    # diagnostic: explain why no suggestions were produced
                    # build filtered pool here for visibility
                    pool = []
                    try:
                        for name, v in selected_entries.items():
                            try:
                                c = v[3]
                            except Exception:
                                continue
                            if not isinstance(c, (int, float)):
                                continue
                            if assign_min_const is not None and c < assign_min_const:
                                continue
                            if assign_max_const is not None and c > assign_max_const:
                                continue
                            pool.append((name, c))
                    except Exception:
                        pool = []

                    diag_lines = [
                        "提案が見つかりませんでした。デバッグ情報:",
                        f"pct: {percent_start} -> {percent_target}",
                        f"aj_max_const: {aj_max_const}",
                        f"assign_min_const: {assign_min_const}",
                        f"assign_max_const: {assign_max_const}",
                        f"選定済み曲数(selected_entries): {len(selected_entries)}",
                        f"フィルタ後候補数(pool): {len(pool)}",
                    ]
                    if pool:
                        diag_lines.append("候補上位5:")
                        diag_lines.extend([f"{n} ({c:.1f})" for n, c in pool[:5]])

                    await ctx.send("\n".join(diag_lines))
        except Exception:
            pass
        
        # 追加診断5: 計算対象曲のタイトルとチャート集計のMAS曲タイトルの差分を取り、重複しないものを表示
        # try:
        #     # selected_lines から Title: を抜き出してセット化
        #     sel_titles = set()
        #     for line in selected_lines:
        #         m = re.match(r"Title:\s*(.*?)\t", line)
        #         if m:
        #             sel_titles.add(m.group(1))

        #     # mas_song_names は上で計算済み。対称差分を取り、重複しないリストにする
        #     diff_titles = sorted(list((sel_titles - mas_song_names) | (mas_song_names - sel_titles)))

        #     if diff_titles:
        #         await ctx.send("選定対象とMASチャート集計の差分（どちらか一方にのみ存在するタイトル・重複なし、最大100件）: " + ", ".join(diff_titles[:100]))
        #     else:
        #         await ctx.send("選定対象とMASチャート集計の差分はありません。")
        # except Exception:
        #     pass
    else:
        await ctx.send("不明な op2 オプションです。'!op help'で利用可能コマンドを確認してください")
        return
    
@bot.command()
async def update(ctx, now: str):
    """Inform the date"""
    if(now=="now"):
        async for message in ctx.channel.history(limit=2):
            if bot.user != ctx.author:
                await message.delete(delay=1.2)
        dt_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
        await ctx.send(f"<@&1272147130743783496>{dt_now.year}年{dt_now.month}月{dt_now.day}日{dt_now.hour}時{dt_now.minute}分{dt_now.second}秒までの更新分を反映しました\n")
    else:
        async for message in ctx.channel.history(limit=1):
            if bot.user != ctx.author:
                await message.delete(delay=1.2)
        await ctx.send(f"<@&1272147130743783496>{now}まで更新したよ！")

@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)

@bot.command()
async def etatoto(ctx, flag: str):
    """send url"""
    th_id = 1350530010058068038
    if(flag==config.SECRET):
        #await ctx.send("ok")
        thread = bot.get_channel(th_id) #get_channel(id):Returns a channel or thread with the given ID.
        await thread.send(ctx.author.mention)
        

@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)

@bot.command()
async def omi(ctx, game: str, diff: str, op: str, op2: str):
    """Randomly select 3 songs from that game"""
    if(game=='c'):
        f = open("data_c.json", 'r')

        json_data = json.load(f)
        u=[]
        #u2=[]
        #u3=[]
        #u4=[]
        #u5=[]
        for v in json_data.values():
            if(op=="s" and v['diff']==diff):
                if(op2=="or" and v['data'][1]=="ORIGINAL"):
                    u.append(v)
                elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                    u.append(v)
                elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11"):
                if(op2=="or" and v['data'][1]=="ORIGINAL"):
                    u.append(v)
                elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                    u.append(v)
                elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11+"):
                if(v['diff']!="11"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12"):
                if(v['diff']!="11" and v['diff']!="11+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14"):
                if(v['diff']=="14" or v['diff']=="14+" or v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14+"):
                if(v['diff']=="14+" or v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15"):
                if(v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15+"):
                if(v['diff']=="15+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15+"):
                if(op2=="or" and v['data'][1]=="ORIGINAL"):
                    u.append(v)
                elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                    u.append(v)
                elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15"):
                if(v['diff']!="15+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14+"):
                if(v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14"):
                if(v['diff']!="14+" and v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13" or v['diff']=="13+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11+"):
                if(v['diff']=="11" or v['diff']=="11+"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11"):
                if(v['diff']=="11"):
                    if(op2=="or" and v['data'][1]=="ORIGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
    elif(game=='o'):
        f = open("data_o.json", 'r')

        json_data = json.load(f)
        u=[]
        for v in json_data.values():
            if(op=="s" and v['diff']==diff):
                if(op2=="on" and v['data'][1]=="オンゲキ"):
                    u.append(v)
                elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11"):
                if(op2=="on" and v['data'][1]=="オンゲキ"):
                    u.append(v)
                elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="11+"):
                if(v['diff']!="11"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12"):
                if(v['diff']!="11" and v['diff']!="11+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="12+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="13+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13" and v['diff']!="13+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="14+"):
                if(v['diff']!="11" and v['diff']!="11+" and v['diff']!="12" and v['diff']!="12+" and v['diff']!="13" and v['diff']!="13+" and v['diff']!="14"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15"):
                if(v['diff']=="15" or v['diff']=="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="h" and diff=="15+"):
                if(v['diff']=="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15+"):
                if(op2=="on" and v['data'][1]=="オンゲキ"):
                    u.append(v)
                elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                    u.append(v)
                elif(op2=="va" and v['data'][1]=="VARIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方Project"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconico"):
                    u.append(v)
                elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                    u.append(v)
                elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                    u.append(v)
                elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="15"):
                if(v['diff']!="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14+"):
                if(v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="14"):
                if(v['diff']!="14+" and v['diff']!="15" and v['diff']!="15+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13" or v['diff']=="13+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="13"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+" or v['diff']=="13"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12+"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12" or v['diff']=="12+"):
                    if(op2=="or" and v['data'][1]=="ORIGINALGINAL"):
                        u.append(v)
                    elif(op2=="ge" and v['data'][1]=="ゲキマイ"):
                        u.append(v)
                    elif(op2=="ir" and v['data'][1]=="イロドリミドリ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="12"):
                if(v['diff']=="11" or v['diff']=="11+" or v['diff']=="12"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11+"):
                if(v['diff']=="11" or v['diff']=="11+"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
            elif(op=="l" and diff=="11"):
                if(v['diff']=="11"):
                    if(op2=="on" and v['data'][1]=="オンゲキ"):
                        u.append(v)
                    elif(op2=="cm" and v['data'][1]=="チュウマイ"):
                        u.append(v)
                    elif(op2=="va" and v['data'][1]=="VARIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方Project"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconico"):
                        u.append(v)
                    elif(op2=="pa" and v['data'][1]=="POPS & ANIME"):
                        u.append(v)
                    elif(op2=="lu" and v['data'][1]=="LUNATIC"):
                        u.append(v)
                    elif(op2=="no"): u.append(v)
    await ctx.send(f"本日の{ctx.author.mention}の課題曲\n")
    for a in range(3):
        answer = random.choice(u)
        await ctx.send("{0}\t Title: {1}\t Difficulty: {2}\t Level: {3}\t Genre: {4}\t CN: {5}\n".format(a+1,answer['name'],answer['diff'],answer['data'][0],answer['data'][1],answer['data'][2]))
        '''
        for a in range(3):
            answer = random.choice(u)
            a1 = answer.values['name']
            await ctx.send(a1)
            #print(answer['name'],end="\t")
            for i in range(3):
                a2 = answer.values['data'][i]
                await ctx.send(a2)
                #print("{}".format(answer['data'][i]),end="\t")
            print("\n")
        '''

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')

@bot.group()
async def cool(ctx):
    """Says if a user is cool.

    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} is not cool')

@cool.command(name='bot')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, the bot is cool.')

# Flaskサーバーをセットアップ
app = Flask('')

@app.route('/')
def home():
    # Renderからのアクセスに対して応答を返す
    return "I'm alive"

def run():
    # Webサーバーを起動する
    # hostを0.0.0.0に、portを環境変数PORTから取得（Renderが自動で設定）
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # RenderのURLを環境変数から取得（なければ何もしない）
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        while True:
            try:
                # 14分ごとに自分自身にアクセス
                time.sleep(14 * 60) 
                requests.get(render_url)
                print("Sent keep-alive ping.")
            except Exception as e:
                print(f"Failed to send keep-alive ping: {e}")

def start_bot():
    bot.run(config.DISCORD_TOKEN)

if __name__ == "__main__":
    # Webサーバーを別のスレッドで起動
    server_thread = Thread(target=run)
    server_thread.start()
    ping_thread = Thread(target=keep_alive)
    ping_thread.start()
    
    # メインスレッドでBotを起動
    start_bot()