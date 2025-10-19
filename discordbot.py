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
        op2 = names[0] if len(names) >= 1 else None
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
            # ensure aj_max_const exists in scope even if not provided
            aj_max_const = None
            tokens = [t for t in parsed_args]
            while i < len(tokens):
                tk = tokens[i]
                low = str(tk).lower()
                if low in ('pct', '--pct', 'percent', '--percent'):
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
                elif low in ('rep-const', '--rep-const', 'repconst', '--repconst'):
                    try:
                        rc = float(tokens[i+1])
                        rep_const_override = rc
                        i += 2
                        continue
                    except Exception:
                        cleaned.append(tk)
                        i += 1
                        continue
                elif low in ('aj-max', 'ajmax', '--aj-max', '--ajmax'):
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
            if str(first).lower() in ("true", "1", "yes", "y", "t"):
                exclude_mode = True
                # build initial raw exclude tokens
                raw_tokens = [n.strip() for n in rest if n and n.strip()]
                # expand any preset group aliases (case-insensitive key match)
                expanded = []
                # If first token is 'custom', treat remaining tokens as literal titles
                if raw_tokens and raw_tokens[0].lower() == 'custom':
                    expanded = raw_tokens[1:]
                else:
                    for tok in raw_tokens:
                        key = tok.lower()
                        if key in PRESET_GROUPS:
                            expanded.extend(PRESET_GROUPS[key])
                        else:
                            expanded.append(tok)
                exclude_set = set(expanded)
            else:
                exclude_mode = False
                all_names = ([first] if first is not None else []) + rest
                raw_tokens = [n.strip() for n in all_names if n and n.strip()]
                # support `custom` as the first token to mean the rest are literal titles
                if raw_tokens and raw_tokens[0].lower() == 'custom':
                    expanded = raw_tokens[1:]
                else:
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

    # Load json if not provided
    if json_data is None:
        try:
            with open("data_c.json", 'r') as f:
                json_data = json.load(f)
        except Exception as e:
            await ctx.send(f"データ読み込みエラー: {e}")
            return

    # default op2 behavior
    if op2 is None or op2 == 'sum':
        # Build helper lookup: name -> list of entries
        name_map = {}
        entries = []
        mas_count = 0
        ult_count = 0
        for v in json_data.values():
            try:
                chart_const = float(v['data'][2])
            except Exception:
                continue
            chart_type = v['data'][0]
            if chart_type in ("ULT", "MAS"):
                # count chart occurrences
                if chart_type == 'MAS':
                    mas_count += 1
                elif chart_type == 'ULT':
                    ult_count += 1
                name = v['name']
                name_map.setdefault(name, []).append((chart_type, chart_const, v.get('diff', '')))
                entries.append((name, chart_const, v.get('diff', ''), chart_type, v['data'][1]))

    # sort by const desc
        entries.sort(key=lambda x: x[1], reverse=True)

        # send MAS/ULT counts summary (raw chart occurrences and unique MAS-song count)
        try:
            await ctx.send(f"チャート集計(合計チャート数): MAS: {mas_count} 曲, ULT: {ult_count} 曲, 合計: {mas_count + ult_count} チャート")
        except Exception:
            # ignore send errors here
            pass

        # Use a map to store the selected entry per song title so we can
        # prefer ULT over MAS and replace previously-added MAS if a ULT is
        # encountered later.
        selected_entries = {}  # name -> (chart_type, max_op, selected_line, const, diffv)
        total_op = 0.0
        processed_mas_selected = 0
        processed_ult_selected = 0
        mas_selected_counts = {}

        for name, const, diffv, chart_type, genre in entries:
            # Exclusion handling first
            if exclude_mode and name in exclude_set:
                if chart_type == 'ULT':
                    # Try to use MAS instead of ULT when exclusion is requested
                    mas_entries = [t for t in name_map.get(name, []) if t[0] == 'MAS']
                    if mas_entries:
                        # use the first MAS entry available
                        mas_const = mas_entries[0][1]
                        max_op = (mas_const + 3) * 5
                        sel_line = f"Title: {name}\tDiff:MAS\tType:MAS\tConst:{mas_const}\tMaxOP:{max_op:.2f}"
                        # If we've already selected something for this name, skip replacing
                        if name in selected_entries:
                            continue
                        selected_entries[name] = ('MAS', max_op, sel_line, mas_const, 'MAS')
                        total_op += max_op
                        processed_mas_selected += 1
                        mas_selected_counts[name] = mas_selected_counts.get(name, 0) + 1
                    else:
                        # No MAS available -> skip entirely
                        continue
                else:
                    # current is MAS and excluded -> skip
                    continue

            else:
                # Normal handling
                max_op = (const + 3) * 5
                sel_line = f"Title: {name}\tDiff:{diffv}\tType:{chart_type}\tConst:{const}\tMaxOP:{max_op:.2f}"

                if name not in selected_entries:
                    # first time selecting this title
                    selected_entries[name] = (chart_type, max_op, sel_line, const, diffv)
                    total_op += max_op
                    if chart_type == 'MAS':
                        processed_mas_selected += 1
                        mas_selected_counts[name] = mas_selected_counts.get(name, 0) + 1
                    elif chart_type == 'ULT':
                        processed_ult_selected += 1
                else:
                    # we already have a selected entry for this title
                    existing_type, existing_op, existing_line, existing_const, existing_diff = selected_entries[name]
                    # If existing is MAS and current is ULT, replace MAS with ULT
                    if existing_type == 'MAS' and chart_type == 'ULT':
                        # remove MAS contribution
                        total_op -= existing_op
                        processed_mas_selected -= 1
                        mas_selected_counts[name] = mas_selected_counts.get(name, 1) - 1
                        if mas_selected_counts.get(name, 0) <= 0:
                            mas_selected_counts.pop(name, None)
                        # add ULT contribution
                        selected_entries[name] = (chart_type, max_op, sel_line, const, diffv)
                        total_op += max_op
                        processed_ult_selected += 1
                    else:
                        # otherwise keep the existing selection (including if existing is ULT)
                        continue

        # Build selected_lines from selected_entries preserving a stable order
        # We'll order by max_op desc so the output is similar to previous behavior
        selected_list = sorted(selected_entries.items(), key=lambda kv: kv[1][1], reverse=True)
        selected_lines = [v[2] for k, v in selected_list]

        try:
            await ctx.send(f"計算対象曲数: {len(selected_lines)} 合計オーバーパワー(Max): {total_op:.2f}\n処理されたMAS曲数(選定): {processed_mas_selected} 曲, 処理されたULT曲数(選定): {processed_ult_selected} 曲")
        except Exception:
            await ctx.send(f"計算対象曲数: {len(selected_lines)} 合計オーバーパワー(Max): {total_op:.2f}")    

        # パーセント指定がある場合、必要なOP差分を計算して表示する
        try:
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
                    await ctx.send(f"百分率指定: {percent_start} -> {percent_target} ({ps*100:.2f}% -> {pt*100:.2f}%)。現在のOP値: {current_value:.2f}、目標値: {target_value:.2f}、必要なOP差: {needed:.2f}")
        except Exception:
            pass

        # 追加提案: 必要OP差からユーザーが増やすべきFC/AJ/AJC数やスコア差を提案する
        try:
            if percent_start is not None and percent_target is not None and abs(needed) > 0.0001:
                # Choose a representative const: prefer the highest const among selected_entries, else average
                consts = [v[3] for v in selected_entries.values() if isinstance(v[3], (int, float))]
                if consts:
                    rep_const = max(consts)
                else:
                    # fallback: use average of all entry consts
                    all_consts = [e[1] for e in entries] if entries else [0]
                    rep_const = sum(all_consts) / max(1, len(all_consts))

                # Formula components per your rules (when score >= 1007501):
                # base = (const + 2) * 5
                base = (rep_const + 2) * 5

                # Each FC adds +0.50, each AJ adds +0.50, each AJC adds +0.25 (AJC stacked on top of AJ/FC)
                #補正B relates to score: (score - 1007500) * 0.0015

                # We'll estimate how many FC/AJ/AJC or how many score points are needed to cover 'needed'.
                remaining = needed
                suggestions = []

                # Optimization search combining 補正A (FC/AJ/AJC) and 補正B (score steps)
                if remaining > 0:
                    # Interpret contributions per unit:
                    # AJ: effectively +1.0 OP (AJ implies FC so stack = 0.5+0.5)
                    # FC: +0.5 OP
                    # AJC: +0.25 OP
                    # score step: we'll use 500-point steps => +0.75 OP per step
                    D = remaining
                    candidates = []

                    # apply override if provided
                    if rep_const_override is not None:
                        rep_const = rep_const_override

                    # determine eligible AJ slots based on aj_max_const if provided
                    eligible_aj_slots = None
                    if aj_max_const is not None:
                        # count number of selected entries with const <= aj_max_const
                        eligible_aj_slots = sum(1 for v in selected_entries.values() if isinstance(v[3], (int, float)) and v[3] <= aj_max_const)

                    # determine eligible slots based on rep_const_override if provided
                    eligible_rep_slots = None
                    if rep_const_override is not None:
                        eligible_rep_slots = sum(1 for v in selected_entries.values() if isinstance(v[3], (int, float)) and v[3] <= rep_const_override)

                    # define cost weights: base costs for actions (lower == cheaper)
                    # We change priorities based on rep_const:
                    # - If rep_const <= 14: prefer AJ and AJC (AJ/AJC cheaper)
                    # - If rep_const > 14: prefer score increase and FC (score/FC cheaper)
                    # Note: boundary choice is rep_const <= 14 => AJ-priority; adjust if you prefer 14 to be in the other group.
                    aj_scale = 1.0 + max(0.0, (rep_const - 11.0)) / (15.4 - 11.0)
                    if rep_const <= 14.5:
                        cost_aj = 0.4 * aj_scale
                        cost_ajc = 0.2
                        cost_fc = 0.5
                        cost_step = 0.8
                    else:
                        cost_aj = 2.0 * aj_scale
                        cost_ajc = 3.0
                        cost_fc = 0.5
                        cost_step = 0.4

                    # search bounds: cap AJ count by eligible slots if provided
                    max_aj_unbounded = min(50, math.ceil(D / 1.0) + 5)
                    # cap AJ by aj_max_const and also by rep_const_override if provided
                    if eligible_aj_slots is not None:
                        max_aj = min(max_aj_unbounded, eligible_aj_slots)
                    else:
                        max_aj = max_aj_unbounded
                    if eligible_rep_slots is not None:
                        max_aj = min(max_aj, eligible_rep_slots)

                    max_steps = min(200, math.ceil(D / 0.75) + 10)

                    for aj_cnt in range(0, max_aj + 1):
                        for steps in range(0, max_steps + 1):
                            op_from_aj_and_steps = aj_cnt * 1.0 + steps * 0.75
                            rem = D - op_from_aj_and_steps
                            # compute candidate FC cap: cannot exceed eligible_rep_slots if rep limit is set
                            computed_fc_cap = min(50, math.ceil(max(0, rem) / 0.5) + 3)
                            if eligible_rep_slots is not None:
                                max_fc = min(computed_fc_cap, eligible_rep_slots)
                            else:
                                max_fc = computed_fc_cap
                            for fc_cnt in range(0, max_fc + 1):
                                op_from_fcs = fc_cnt * 0.5
                                rem2 = rem - op_from_fcs
                                if rem2 <= 0:
                                    ajc_cnt = 0
                                else:
                                    ajc_cnt = math.ceil(rem2 / 0.25)

                                total_op_provided = aj_cnt * 1.0 + steps * 0.75 + fc_cnt * 0.5 + ajc_cnt * 0.25
                                if total_op_provided < D:
                                    continue
                                # enforce per-action slot limits if rep-const restriction exists
                                if eligible_rep_slots is not None:
                                    if aj_cnt > eligible_rep_slots or fc_cnt > eligible_rep_slots or ajc_cnt > eligible_rep_slots:
                                        continue

                                total_cost = aj_cnt * cost_aj + fc_cnt * cost_fc + ajc_cnt * cost_ajc + steps * cost_step
                                overshoot = total_op_provided - D
                                candidate = (total_cost, overshoot, aj_cnt, fc_cnt, ajc_cnt, steps)
                                candidates.append(candidate)

                    # pick top N candidates by (cost, overshoot)
                    if candidates:
                        candidates.sort(key=lambda c: (c[0], c[1]))
                        top_n = candidates[:3]
                        plan_msgs = []
                        rep_limit_val = rep_const_override if rep_const_override is not None else rep_const
                        pool_titles_all = [name for name, v in selected_entries.items() if isinstance(v[3], (int, float)) and v[3] <= rep_limit_val]

                        for idx, cand in enumerate(top_n, start=1):
                            cost, overshoot, caj, cfc, cajc, csteps = cand
                            msgs = []
                            if caj:
                                msgs.append(f"AJ を +{caj} 回")
                            if cfc:
                                msgs.append(f"FC を +{cfc} 回")
                            if cajc:
                                msgs.append(f"AJC を +{cajc} 回")
                            if csteps:
                                msgs.append(f"スコアを {csteps * 500} 点増加する目安 ({csteps} ステップ)")

                            # build assignment from pool
                            assign_msg = ''
                            try:
                                pool_titles = list(pool_titles_all)
                                random.shuffle(pool_titles)
                                if not pool_titles:
                                    assign_msg = "\n注: 指定された代表定数以下の候補曲が見つかりません。曲名割当はできません。"
                                else:
                                    aj_selected = random.sample(pool_titles, min(caj, len(pool_titles))) if caj else []
                                    fc_selected = list(aj_selected)
                                    if cfc:
                                        remaining_pool = [t for t in pool_titles if t not in fc_selected]
                                        take2 = min(cfc - len(fc_selected), len(remaining_pool)) if cfc > len(fc_selected) else 0
                                        if take2 > 0:
                                            fc_selected.extend(random.sample(remaining_pool, take2))
                                        while len(fc_selected) < cfc and pool_titles:
                                            fc_selected.append(random.choice(pool_titles))

                                    ajc_selected = []
                                    if cajc:
                                        remaining_pool = [t for t in pool_titles if t not in aj_selected]
                                        take3 = min(cajc, len(remaining_pool))
                                        if take3 > 0:
                                            ajc_selected = random.sample(remaining_pool, take3)
                                        while len(ajc_selected) < cajc and pool_titles:
                                            ajc_selected.append(random.choice(pool_titles))

                                    score_targets = []
                                    if csteps:
                                        take4 = min(csteps, len(pool_titles))
                                        if take4 > 0:
                                            score_targets = random.sample(pool_titles, take4)

                                    lines = []
                                    if aj_selected:
                                        lines.append("AJ (判定強化) 対象例: " + ", ".join(aj_selected))
                                    if fc_selected:
                                        lines.append("FC (フルコン) 対象例: " + ", ".join(fc_selected))
                                    if ajc_selected:
                                        lines.append("AJC (小判定改善) 対象例: " + ", ".join(ajc_selected))
                                    if score_targets:
                                        lines.append("スコア注力候補: " + ", ".join(score_targets))

                                    assign_msg = "\n割当候補:\n" + "\n".join(lines)
                            except Exception:
                                assign_msg = "\n曲名割当の生成中にエラーが発生しました。"

                            header = f"最小化プラン候補 #{idx} (コスト {cost:.2f}, オーバー {overshoot:.3f} OP):\n"
                            body = " / ".join(msgs) + f"\n想定オーバー分: {overshoot:.3f} OP"
                            if eligible_aj_slots is not None:
                                body += f"\n注: AJ候補は定数 <= {aj_max_const:.2f} の譜面 {eligible_aj_slots} 曲に制限されています。"
                            plan_msgs.append(header + body + assign_msg)

                        # send combined message (up to 3 plans)
                        await ctx.send("\n\n".join(plan_msgs))
                    else:
                        await ctx.send("最小変更プランを算出できませんでした。")
                    # best = None
                    # D = remaining
                    # # Set reasonable search bounds
                    # max_aj = min(100, math.ceil(D / 1.0) + 5)
                    # max_steps = min(200, math.ceil(D / 0.75) + 10)

                    # for aj_cnt in range(0, max_aj + 1):
                    #     for steps in range(0, max_steps + 1):
                    #         op_from_aj_and_steps = aj_cnt * 1.0 + steps * 0.75
                    #         rem = D - op_from_aj_and_steps
                    #         if rem <= 0:
                    #             fc_needed = 0
                    #             ajc_needed = 0
                    #         else:
                    #             # Greedy: prefer FC (0.5 per unit) over AJC (0.25) for lower count
                    #             fc_needed = math.ceil(rem / 0.5)
                    #             ajc_needed = 0

                    #         total_actions = aj_cnt + steps + fc_needed + ajc_needed
                    #         total_op_provided = aj_cnt * 1.0 + steps * 0.75 + fc_needed * 0.5 + ajc_needed * 0.25
                    #         # minimize total actions, then minimize overshoot
                    #         overshoot = total_op_provided - D
                    #         candidate = (total_actions, overshoot, aj_cnt, fc_needed, ajc_needed, steps)
                    #         if best is None:
                    #             best = candidate
                    #         else:
                    #             if candidate[0] < best[0] or (candidate[0] == best[0] and candidate[1] < best[1]):
                    #                 best = candidate

                    # # Also consider pure score-only solution (no actions) using arbitrary finer steps
                    # score_only_steps = math.ceil(D / 0.75)
                    # score_only_actions = score_only_steps
                    # score_candidate = (score_only_actions, score_only_steps * 0.75 - D, 0, 0, 0, score_only_steps)
                    # if best is None or score_candidate[0] < best[0] or (score_candidate[0] == best[0] and score_candidate[1] < best[1]):
                    #     best = score_candidate

                    # if best:
                    #     _, overshoot, best_aj, best_fc, best_ajc, best_steps = best
                    #     msgs = []
                    #     if best_aj:
                    #         msgs.append(f"AJ を +{best_aj} 回 (AJ 含めて1回で +1.0 OP 相当)")
                    #     if best_fc:
                    #         msgs.append(f"FC を +{best_fc} 回 (1回で +0.5 OP)")
                    #     if best_ajc:
                    #         msgs.append(f"AJC を +{best_ajc} 回 (1回で +0.25 OP)")
                    #     if best_steps:
                    #         msgs.append(f"スコアを {best_steps * 500} 点増加する目安 (500点ごとに +0.75 OP, {best_steps} ステップ)")

                    #     await ctx.send("最小変更プラン（推定） - 代表譜面定数 {:.2f} を想定:\n".format(rep_const) + " / ".join(msgs) + f"\n想定オーバー分: {overshoot:.3f} OP")
                    # else:
                    #     await ctx.send("最小変更プランを算出できませんでした。")
                else:
                    await ctx.send("必要OP差が負またはゼロです。増加提案は不要です。")
        except Exception:
            pass
        
        # 追加診断5: 計算対象曲のタイトルとチャート集計のMAS曲タイトルの差分を取り、重複しないものを表示
        try:
            # selected_lines から Title: を抜き出してセット化
            sel_titles = set()
            for line in selected_lines:
                m = re.match(r"Title:\s*(.*?)\t", line)
                if m:
                    sel_titles.add(m.group(1))

            # mas_song_names は上で計算済み。対称差分を取り、重複しないリストにする
            diff_titles = sorted(list((sel_titles - mas_song_names) | (mas_song_names - sel_titles)))

            if diff_titles:
                await ctx.send("選定対象とMASチャート集計の差分（どちらか一方にのみ存在するタイトル・重複なし、最大100件）: " + ", ".join(diff_titles[:100]))
            else:
                await ctx.send("選定対象とMASチャート集計の差分はありません。")
        except Exception:
            pass
    else:
        await ctx.send("不明な op2 オプションです。'sum' を指定するか省略してください。")
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
                elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                    u.append(v)
                elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                    u.append(v)
                elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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
                    elif(op2=="va" and v['data'][1]=="VARIETYIETY"):
                        u.append(v)
                    elif(op2=="to" and v['data'][1]=="東方ProjectProject"):
                        u.append(v)
                    elif(op2=="ni" and v['data'][1]=="niconiconiconico"):
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