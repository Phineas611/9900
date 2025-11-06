import io, uuid, time, json, os, logging, re
import asyncio
import httpx
from typing import Dict, Any, List, Tuple
from fastapi import UploadFile
import pandas as pd

from sqlalchemy.orm import Session
from app.persistence.evaluation_repository import EvaluationRepository
from app.application.models.evaluation import AssessRequest, Verdict
from app.presentation.routes.rubric import build_prompt, build_batch_prompt, make_verdicts_schema, language_tool_check
from app.integration.judges.groq_llama31_8b import GroqLlama31_8B_Judge
from app.integration.judges.groq_llama33_70b import GroqLlama33_70B_Judge
from app.integration.judges.hf_prometheus2_7b import HFPrometheus2_7B_Judge
from app.utils.aggregation import majority_label, dawid_skene_binary
from app.utils.anchors import load_anchor_lexicon, compile_anchor_patterns, match_anchor
from app.utils.reliability import fleiss_kappa, cohens_kappa, CATS

REQUIRED_COLUMNS = {
    "item_id": ["item_id", "id", "row_id"],
    "sentence": ["sentence", "text"],
    # gold_label Change to "Optional Column"
    "predicted_label": ["predicted_label", "pred", "prediction"],
    "rationale": ["rationale", "reason", "explanation"],
}

class EvaluationService:
    def __init__(self, repo: EvaluationRepository):
        self.repo = repo
        self._logger = logging.getLogger(__name__)
        # configurable anchor lexicon: env ANCHOR_LEXICON_PATH or default file
        default_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'anchors.json')
        lex_path = os.getenv('ANCHOR_LEXICON_PATH', default_path)
        self._anchor_patterns = compile_anchor_patterns(load_anchor_lexicon(lex_path))
        # concurrency knobs (env overrides):
        self._item_concurrency = int(os.getenv("EVAL_ITEM_CONCURRENCY", "4"))
        self._judge_concurrency = int(os.getenv("EVAL_JUDGE_CONCURRENCY", "8"))
        self._batch_size = int(os.getenv("EVAL_BATCH_SIZE", "8"))
        self._groq_url = "https://api.groq.com/openai/v1/chat/completions"

    # ---------- UPLOAD ----------
    def upload_file(self, db: Session, user_id: int, file: UploadFile) -> Dict[str, Any]:
        content = file.file.read()
        name = file.filename or "uploaded"
        # load CSV/XLSX
        if name.lower().endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))

        colmap = {}
        for key, candidates in REQUIRED_COLUMNS.items():
            for c in candidates:
                for real in df.columns:
                    if real.strip().lower() == c:
                        colmap[key] = real
                        break
                if key in colmap:
                    break
        missing = [k for k in REQUIRED_COLUMNS.keys() if k not in colmap]
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Found columns={list(df.columns)}")


        gold_col = None
        for cand in ["gold_label", "gold", "label"]:
            for real in df.columns:
                if real.strip().lower() == cand:
                    gold_col = real
                    break
            if gold_col:
                break

        run_id = str(uuid.uuid4())
        # persist run & items
        config = {"columns_mapped": colmap}
        run = self.repo.create_run(db, run_id=run_id, user_id=user_id, file_name=name, config=config)

        rows = []
        for _, r in df.iterrows():
            row = {
                "item_id": str(r[colmap["item_id"]]),
                "sentence": str(r[colmap["sentence"]]),
                "predicted_label": str(r[colmap["predicted_label"]]),
                "rationale": str(r[colmap["rationale"]]),
            }
            if gold_col:
                row["gold_label"] = str(r[gold_col])
            rows.append(row)
        self.repo.bulk_insert_items(db, run_id, rows)

        return {
            "run_id": run_id,
            "file_name": name,
            "total_items": len(rows),
            "columns_mapped": colmap
        }

    # ---------- ASSESS ----------
    def _make_judges(self, ids: List[str]):
        out = []
        for mid in ids:
            if mid.startswith("groq/llama-3.1-8b"):
                out.append(GroqLlama31_8B_Judge())
            elif mid.startswith("groq/llama-3.3-70b") and os.getenv("GROQ_DISABLE_70B", "0") != "1":
                out.append(GroqLlama33_70B_Judge())
            elif mid.startswith("hf/prometheus-7b-v2.0"):
                out.append(HFPrometheus2_7B_Judge())
        return out

    # ---------- Async helpers ----------
    def _normalize_verdict(self, data: Dict[str, Any], dim_keys: List[str], manual_metrics: List[str]) -> Dict[str, Any]:
        rubric = data.get("rubric", {})
        manual = data.get("manual", {})
        from app.utils.reliability import CATS
        jlabel = str(data.get("judge_label", "ambiguous")).strip().lower()
        if jlabel not in CATS:
            jlabel = "ambiguous"
        def _coerce_conf(x: Any) -> float:
            try:
                v = float(x)
            except Exception:
                v = 0.5
            # clip to [0,1]
            if v < 0.0:
                v = 0.0
            elif v > 1.0:
                v = 1.0
            return v
        return {
            "judge_label": jlabel,
            "predicted_class_correct": data.get("predicted_class_correct"),
            "rubric": {
                k: {
                    "pass": bool((rubric.get(k) or {}).get("pass", True)),
                    "confidence": _coerce_conf((rubric.get(k) or {}).get("confidence", None)),
                    "notes": str((rubric.get(k) or {}).get("notes", ""))[:30],
                } for k in dim_keys
            },
            "manual": {
                m: {
                    "pass": bool((manual.get(m) or {}).get("pass", True)),
                    "confidence": _coerce_conf((manual.get(m) or {}).get("confidence", None)),
                    "notes": str((manual.get(m) or {}).get("notes", ""))[:30],
                } for m in manual_metrics
            }
        }

    async def _groq_batch(self, model: str, items: List[Dict[str, Any]], dim_keys: List[str], manual_metrics: List[str],
                          temperature: float, require_json: bool, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> Dict[str, Any]:
        prompt = build_batch_prompt(items, {k: True for k in dim_keys}, manual_metrics, require_json=require_json)
        schema = make_verdicts_schema(dim_keys, manual_metrics) if require_json else None
        headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY','')}"}
        max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "192"))
        min_interval_ms = int(os.getenv("GROQ_MIN_INTERVAL_MS", "150"))
        req = {
            "model": model.split("/")[-1],
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": "You are a strict evaluation judge. Output ONLY JSON."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
        }
        model_short = req["model"]
        if schema:
            # Prefer json_schema, but some models (e.g., llama-3.1-8b-instant) do not support it.
            supports_schema = not ("llama-3.1-8b" in model_short)
            req["response_format"] = (
                {"type": "json_schema", "json_schema": schema} if supports_schema else {"type": "json_object"}
            )
        else:
            req["response_format"] = {"type": "json_object"}
        t0 = time.time()
        self._logger.info(f"GROQ batch request: model={req['model']}, items={len(items)}, require_json={require_json}")
        self._logger.info(f"GROQ response_format: {req.get('response_format')}")
        # 令牌桶：按批次提示长度估算令牌占用，避免 TPM 撞限
        try:
            from app.integration.judges.rate_limit import estimate_tokens_from_text, acquire_capacity_async, get_async_sem
            prompt_text = prompt
            required_tokens = estimate_tokens_from_text(prompt_text, max_output=max_tokens, extra=64)
        except Exception:
            required_tokens = max_tokens * 2
        await acquire_capacity_async(req["model"], required_tokens)
        # 重试与降级：429/5xx 退避；如使用 json_schema 且失败，降级到 json_object
        max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))
        attempt = 0
        degraded = False

        async def _do_post():
            async with get_async_sem(req["model"]):
                await asyncio.sleep(min_interval_ms / 1000.0)
                return await client.post(self._groq_url, headers=headers, json=req, timeout=60)

        def _parse_retry_wait(resp) -> float:
            ra = resp.headers.get("Retry-After")
            if ra:
                try:
                    return float(ra)
                except Exception:
                    pass
            try:
                data = resp.json()
                msg = (data.get("error") or {}).get("message") or ""
            except Exception:
                msg = getattr(resp, "text", "") or ""
            m = re.search(r"try again in\s+(\d+(?:\.\d+)?)\s*ms", msg, re.IGNORECASE)
            if m:
                return float(m.group(1)) / 1000.0
            m = re.search(r"try again in\s+(\d+(?:\.\d+)?)\s*s", msg, re.IGNORECASE)
            if m:
                return float(m.group(1))
            return 0.5

        resp = None
        while attempt <= max_retries:
            async with sem:
                resp = await _do_post()
            self._logger.info(f"GROQ status_code={resp.status_code}")
            try:
                self._logger.info(f"GROQ resp_text={resp.text[:400]}")
            except Exception:
                pass

            if resp.status_code == 200:
                break

            # 如使用 json_schema 并遇非 200，先降级到 json_object 再试
            if isinstance(req.get("response_format"), dict) and req["response_format"].get("type") == "json_schema" and not degraded:
                self._logger.info("Non-200 under json_schema; degrading to json_object and retrying")
                req["response_format"] = {"type": "json_object"}
                degraded = True
                attempt += 1
                continue

            # 429/5xx 退避重试
            if resp.status_code in (429, 500, 502, 503, 504):
                base = _parse_retry_wait(resp)
                backoff = min(max(base, 0.25), 2.0) * (1 + attempt * 0.5)
                self._logger.info(f"GROQ backoff sleeping {backoff:.2f}s (attempt={attempt})")
                await asyncio.sleep(backoff)
                attempt += 1
                continue
            # 其他错误不重试
            break
        # Parse provider response safely; fallback if schema/choices missing
        try:
            data = resp.json()
        except Exception as e:
            data = {"error": f"resp_json_error: {e}", "status_code": getattr(resp, 'status_code', None)}

        def _invalid_verdict() -> Dict[str, Any]:
            return {
                "judge_label": None,
                "predicted_class_correct": None,
                "rubric": {},
                "manual": {},
            }

        try:
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise KeyError("choices")
            content = choices[0]["message"]["content"]
            # Groq structured outputs still return string content; parse to list
            def _flatten_list(x):
                out = []
                for e in x:
                    if isinstance(e, list):
                        out.extend(_flatten_list(e))
                    else:
                        out.append(e)
                return out
            try:
                arr = json.loads(content)
                if isinstance(arr, list):
                    arr = _flatten_list(arr)
                else:
                    arr = [arr]
            except Exception:
                # best-effort fallback: try to find first [...] block
                txt = content
                start, end = txt.find("["), txt.rfind("]")
                arr = json.loads(txt[start:end+1]) if start != -1 and end != -1 else []
                if isinstance(arr, list):
                    arr = _flatten_list(arr)
            # keep only dicts
            arr = [e for e in arr if isinstance(e, dict)]
            # Adjust length to match input items (pad missing entries as invalid)
            if len(arr) < len(items):
                arr = arr + [_invalid_verdict() for _ in range(len(items) - len(arr))]
            elif len(arr) > len(items):
                arr = arr[:len(items)]
            if not arr:
                arr = [_invalid_verdict() for _ in items]
            return {"latency_ms": (time.time()-t0)*1000, "provider_raw": data, "verdicts": arr}
        except Exception as e:
            # Provider error or missing structured output; mark items invalid and continue
            return {
                "latency_ms": (time.time()-t0)*1000,
                "provider_raw": {"error": str(e), "raw": data},
                "verdicts": [_invalid_verdict() for _ in items]
            }

    def _chunk(self, seq: List[Any], size: int) -> List[List[Any]]:
        return [seq[i:i+size] for i in range(0, len(seq), max(1, size))]

    async def _judge_two_then_maybe_third_batch(self, db: Session, run_id: str, batch_items: List[Any],
                                                req: AssessRequest, dim_keys: List[str], manual_metrics: List[str],
                                                client: httpx.AsyncClient, judge_sem: asyncio.Semaphore) -> Tuple[List[List[str]], List[str | None]]:
        # 三位评委同时判（若少于三位则退化为两位）
        j1_id = req.judge_models[0]
        j2_id = req.judge_models[1] if len(req.judge_models) > 1 else req.judge_models[0]
        j3_id = req.judge_models[2] if len(req.judge_models) > 2 else None

        inputs = [{"sentence": it.sentence, "rationale": it.rationale} for it in batch_items]

        def _is_groq(mid: str) -> bool:
            return mid.startswith("groq/") or mid.startswith("groq:")

        # 为同步评委准备逐条 prompt（Groq 走批量）
        prompts: List[str] = []
        if True:
            prompts = []
            for it in batch_items:
                lt = language_tool_check(it.rationale)
                prompts.append(build_prompt({"sentence": it.sentence, "rationale": it.rationale},
                                            req.criteria, manual_metrics, lt, req.require_json))

        async def run_sync(judge_id: str, prompts: List[str]) -> Dict[str, Any]:
            judges = self._make_judges([judge_id])
            if not judges:
                self._logger.warning(f"[eval] No sync judge available for {judge_id}, skipping.")
                invalid = {"judge_label": None, "predicted_class_correct": None, "rubric": {}, "manual": {}}
                return {"latency_ms": 0.0, "provider_raw": {}, "verdicts": [invalid for _ in prompts]}
            j = judges[0]
            async def one(p):
                return await asyncio.to_thread(j.judge, {"prompt": p, "temperature": req.temperature})
            t0 = time.time()
            outs = [await one(p) for p in prompts]
            return {"latency_ms": (time.time()-t0)*1000, "provider_raw": {}, "verdicts": [json.loads(o["json"]) for o in outs]}

        # 启动三位评委任务（Groq 批量；非 Groq 同步回退）
        j1_task = self._groq_batch(j1_id, inputs, dim_keys, manual_metrics, req.temperature, req.require_json, client, judge_sem) if _is_groq(j1_id) else run_sync(j1_id, prompts)
        j2_task = self._groq_batch(j2_id, inputs, dim_keys, manual_metrics, req.temperature, req.require_json, client, judge_sem) if _is_groq(j2_id) else run_sync(j2_id, prompts)
        j3_task = None
        if j3_id:
            j3_task = self._groq_batch(j3_id, inputs, dim_keys, manual_metrics, req.temperature, req.require_json, client, judge_sem) if _is_groq(j3_id) else run_sync(j3_id, prompts)

        # 并发收集所有结果
        if j3_task:
            j1_res, j2_res, j3_res = await asyncio.gather(j1_task, j2_task, j3_task)
        else:
            j1_res, j2_res = await asyncio.gather(j1_task, j2_task)
            j3_res = None

        # 归一化所有裁决
        j1_verdicts = [self._normalize_verdict(v, dim_keys, manual_metrics) for v in j1_res["verdicts"]]
        j2_verdicts = [self._normalize_verdict(v, dim_keys, manual_metrics) for v in j2_res["verdicts"]]
        j3_verdicts = ([self._normalize_verdict(v, dim_keys, manual_metrics) for v in j3_res["verdicts"]] if j3_res else [])

        # 落库三位评委裁决
        for it, v1, v2 in zip(batch_items, j1_verdicts, j2_verdicts):
            self.repo.add_judgment(db, run_id, it.id, j1_id, v1, j1_res["latency_ms"], j1_res.get("provider_raw", {}))
            self.repo.add_judgment(db, run_id, it.id, j2_id, v2, j2_res["latency_ms"], j2_res.get("provider_raw", {}))
        if j3_id and j3_verdicts:
            for it, v3 in zip(batch_items, j3_verdicts):
                self.repo.add_judgment(db, run_id, it.id, j3_id, v3, (j3_res or {}).get("latency_ms", 0.0), (j3_res or {}).get("provider_raw", {}))

        # 汇总三位评委的类别投票与 anchors
        all_votes: List[List[str]] = []
        anchor_priors: List[str | None] = []
        for idx, it in enumerate(batch_items):
            prior = match_anchor(f"{it.sentence} {it.rationale}", self._anchor_patterns)
            anchor_priors.append(prior)
            l1 = j1_verdicts[idx]["judge_label"]
            l2 = j2_verdicts[idx]["judge_label"]
            row = [l1, l2]
            if j3_id and j3_verdicts:
                row.append(j3_verdicts[idx]["judge_label"])
            all_votes.append(row)

        return all_votes, anchor_priors
    async def assess_async(self, db: Session, user_id: int, req: AssessRequest) -> Dict[str, Any]:
        # 统一归一化 judge 模型别名，避免分流判断失败
        alias = {
            # 前端占位符映射到真实模型；支持环境变量覆盖
            "judge-mini-a": os.getenv("JUDGE_MINI_A_MODEL", "groq/llama-3.1-8b-instant"),
            "judge-mini-b": os.getenv("JUDGE_MINI_B_MODEL", "hf/prometheus-7b-v2.0"),
            "judge-mini-c": os.getenv("JUDGE_PRO_MODEL", "groq/llama-3.3-70b-versatile"),
            # 常见写法归一化
            "groq_llama31_8b": "groq/llama-3.1-8b-instant",
            "groq_llama33_70b": "groq/llama-3.3-70b-versatile",
            "llama-3.1-8b": "groq/llama-3.1-8b-instant",
            "llama-3.3-70b": "groq/llama-3.3-70b-versatile",
        }
        if getattr(req, "judge_models", None):
            req.judge_models = [alias.get(m.strip(), m.strip()) for m in req.judge_models]
            # 过滤未知 ID，并自动补齐到 3 个（Groq 走批量；HF Prometheus 走同步）
            def _is_groq(mid: str) -> bool:
                return mid.startswith("groq/") or mid.startswith("groq:")
            SUPPORTED_SYNC = {"hf/prometheus-7b-v2.0"}
            final = [m for m in req.judge_models if _is_groq(m) or m in SUPPORTED_SYNC]
            defaults = [
                os.getenv("JUDGE_MINI_A_MODEL", "groq/llama-3.1-8b-instant"),
                "hf/prometheus-7b-v2.0",
                os.getenv("JUDGE_PRO_MODEL", "groq/llama-3.3-70b-versatile"),
            ]
            for d in defaults:
                if len(final) >= 3:
                    break
                if d not in final and (_is_groq(d) or d in SUPPORTED_SYNC):
                    final.append(d)
            req.judge_models = final
            self._logger.info(f"judge_models(finalized)={req.judge_models}")
        run = self.repo.get_run(db, req.run_id)
        if not run:
            raise ValueError("run not found")
        self.repo.update_run_status(db, req.run_id, "PROCESSING")

        items = self.repo.list_items(db, req.run_id, 0, req.page_limit)
        dim_keys = [k for k, v in req.criteria.items() if v]

        all_item_votes: List[List[str]] = []
        anchor_priors_all: List[str | None] = []

        item_batches = self._chunk(items, self._batch_size)
        judge_sem = asyncio.Semaphore(self._judge_concurrency)

        async with httpx.AsyncClient() as client:
            async def process_batch(batch):
                votes, priors = await self._judge_two_then_maybe_third_batch(db, req.run_id, batch, req, dim_keys, req.manual_metrics, client, judge_sem)
                # After judgments saved, compute aggregates per item from saved verdicts simply by reusing logic akin to sync assess
                # We will recompute yes/no by majority among available judges using repository list_judgments_for_item
                for it in batch:
                    js = self.repo.list_judgments_for_item(db, req.run_id, it.id)
                    judge_votes = {d: {} for d in dim_keys}
                    votes_count = {}
                    confidences = {}
                    supporter_conf_sum = {}
                    notes = {}
                    used_models = []
                    judge_cls_votes: List[str] = []
                    for j in js:
                        used_models.append(j.judge_model)
                        data = j.verdict
              
                        raw_jlabel = data.get("judge_label", None)
                        jlabel = (str(raw_jlabel).strip().lower() if isinstance(raw_jlabel, str) else None)
                        if jlabel in CATS:
                            judge_cls_votes.append(jlabel)
                        for d in dim_keys:
                            leaf = (data.get("rubric", {}).get(d) or {})
              
                            rawc = leaf.get("confidence", None)
                            try:
                                c = float(rawc)
                                if c < 0.0:
                                    c = 0.0
                                elif c > 1.0:
                                    c = 1.0
                            except Exception:
                                c = None
                            p = leaf.get("pass", None)
                            n = str(leaf.get("notes", ""))[:30]
                            if isinstance(p, bool):
                                judge_votes[d][j.judge_model] = p
                                votes_count[d] = votes_count.get(d, 0) + (1 if p else 0)
                                if isinstance(c, float):
                                    confidences[d] = confidences.get(d, 0.0) + c
                                    if p:
                                        supporter_conf_sum[d] = supporter_conf_sum.get(d, 0.0) + c
                            notes[d] = (notes.get(d, "") + f" | {j.judge_model}: {n}").strip(" |")[:30]

                    yesno = {}; conf = {}
      
                    for d in dim_keys:
                        y = votes_count.get(d, 0)
                        total_present = sum(1 for m in judge_votes.get(d, {}).values())
                        if total_present == 0:
                            yesno[d] = None
                            conf[d] = None
                        else:
                            yes = y >= (total_present // 2 + 1) if total_present > 2 else y >= 1
                            yesno[d] = yes
                            vote_strength = (y / total_present)
                            avg_conf = (supporter_conf_sum.get(d, 0.0) / max(1, y)) if y > 0 else None
                            conf[d] = (round(vote_strength * avg_conf, 3) if avg_conf is not None else None)

                    agg_label, counts, tie = majority_label(judge_cls_votes)
                    class_agree = (str(it.predicted_label).lower() == agg_label.lower()) if getattr(it, "predicted_label", None) else None
                    needs_review = bool(tie or (len(set(judge_cls_votes)) > 1))
                    self.repo.upsert_aggregate(db, req.run_id, it.id, yesno=yesno, confidence=conf, notes=notes, judge_votes=judge_votes, time_ms=0.0,
                                               agg_label=agg_label, class_agreement=class_agree, needs_review=needs_review)

                return votes, priors

            # Item-level concurrency via semaphore wrapper
            item_sem = asyncio.Semaphore(self._item_concurrency)
            async def run_one(batch):
                async with item_sem:
                    return await process_batch(batch)

            results = await asyncio.gather(*[run_one(b) for b in item_batches])
            for votes, priors in results:
                all_item_votes.extend(votes)
                anchor_priors_all.extend(priors)

        # Summary: reuse aggregates table
        acc_numer = 0
        acc_denom = max(1, len(items))
        pass_rates = {k: 0 for k in dim_keys}
        pairs, total = self.repo.list_results(db, req.run_id, page=1, page_size=acc_denom)
        for item, agg in pairs:
            if getattr(agg, "class_agreement", None):
                acc_numer += 1
            for d in dim_keys:
                pass_rates[d] += 1 if agg.yesno.get(d) else 0

        try:
            ds_labels = dawid_skene_binary(all_item_votes, priors=anchor_priors_all) if all_item_votes else None
        except Exception:
            ds_labels = None

        fleiss = fleiss_kappa(all_item_votes) if all_item_votes else None
        pair_cohen: Dict[str, float] = {}
        if all_item_votes:
            cols = list(zip(*all_item_votes))
            if len(cols) >= 2:
                pair_cohen["12"] = cohens_kappa(list(cols[0]), list(cols[1]))
            if len(cols) >= 3:
                pair_cohen["13"] = cohens_kappa(list(cols[0]), list(cols[2]))
                pair_cohen["23"] = cohens_kappa(list(cols[1]), list(cols[2]))

        return {
            "anchors": {
                "ambiguous_seed": sum(1 for p in anchor_priors_all if p == "ambiguous"),
                "unambiguous_seed": sum(1 for p in anchor_priors_all if p == "unambiguous"),
                "none": sum(1 for p in anchor_priors_all if p is None),
            },
            "ds_em": {
                "enabled": bool(ds_labels),
                "diff_rate_vs_majority": 0.0 if not ds_labels else round(
                    sum(1 for (mv, ds) in zip([majority_label(v)[0] for v in all_item_votes], ds_labels) if mv != ds) / max(1, len(ds_labels)), 3
                )
            },
            "kappa": {"fleiss": fleiss, "cohen_pairs": pair_cohen},
            "acc_vs_pred": round(acc_numer / acc_denom, 3) if acc_denom else None,
            "pass_rates": {d: round(pass_rates[d] / acc_denom, 3) for d in dim_keys}
        }

    def assess(self, db: Session, user_id: int, req: AssessRequest) -> Dict[str, Any]:
        run = self.repo.get_run(db, req.run_id)
        if not run:
            raise ValueError("run not found")
        self.repo.update_run_status(db, req.run_id, "PROCESSING")

        judges = self._make_judges(req.judge_models)
        items = self.repo.list_items(db, req.run_id, 0, req.page_limit)
        # Run 级一致性累积器 + anchors 先验
        all_item_votes: List[List[str]] = []
        anchor_priors: List[str | None] = []
        

        t0 = time.time()
        dim_keys = [k for k, v in req.criteria.items() if v]
        for it in items:
            # build prompt with grammar evidence
            lt = language_tool_check(it.rationale)
            prompt = build_prompt(
                {"sentence": it.sentence, "rationale": it.rationale},
                req.criteria, req.manual_metrics, lt, req.require_json
            )

            text_for_anchor = f"{it.sentence} {it.rationale}"
            prior = match_anchor(text_for_anchor, self._anchor_patterns)
            anchor_priors.append(prior)
            # call judges
            votes = {}
            confidences = {}
            supporter_conf_sum = {}
            notes = {}
            judge_votes = {d: {} for d in dim_keys}


            judge_cls_votes: List[str] = []
            for j in judges:
                res = j.judge({"prompt": prompt, "temperature": req.temperature})
                try:
                    data = json.loads(res["json"]) 
                except Exception:
  
                    txt = res["json"]
                    start, end = txt.find("{"), txt.rfind("}")
                    data = json.loads(txt[start:end+1]) if start != -1 and end != -1 else {
                        "judge_label": None,
                        "rubric": {},
                        "manual": {}
                    }

                # normalize
                rubric = data.get("rubric", {})
                manual = data.get("manual", {})

                raw_jlabel = data.get("judge_label", None)
                jlabel = (str(raw_jlabel).strip().lower() if isinstance(raw_jlabel, str) else None)
                if jlabel not in CATS:
                    jlabel = None
                if jlabel is not None:
                    judge_cls_votes.append(jlabel)


                def _as_bool(x: Any) -> bool | None:
                    return x if isinstance(x, bool) else None
                def _as_conf(x: Any) -> float | None:
                    try:
                        v = float(x)
                    except Exception:
                        return None
                    if v < 0.0:
                        v = 0.0
                    elif v > 1.0:
                        v = 1.0
                    return v

                verdict_obj = {
                    "judge_label": jlabel,

                    "predicted_class_correct": data.get("predicted_class_correct"),
                    "rubric": {
                        k: {
                            "pass": _as_bool((rubric.get(k) or {}).get("pass", None)),
                            "confidence": _as_conf((rubric.get(k) or {}).get("confidence", None)),
                            "notes": str((rubric.get(k) or {}).get("notes", ""))[:30],
                        } for k in dim_keys
                    },
                    "manual": {
                        m: {
                            "pass": _as_bool((manual.get(m) or {}).get("pass", None)),
                            "confidence": _as_conf((manual.get(m) or {}).get("confidence", None)),
                            "notes": str((manual.get(m) or {}).get("notes", ""))[:30],
                        } for m in req.manual_metrics
                    }
                }
                self.repo.add_judgment(db, req.run_id, it.id, j.model_id, verdict_obj, res["latency_ms"], res.get("provider_raw", {}))

                # accumulate
                present_count: Dict[str, int] = {}
                for d in dim_keys:
                    p = verdict_obj["rubric"][d]["pass"]
                    c = verdict_obj["rubric"][d]["confidence"]
                    n = verdict_obj["rubric"][d]["notes"]

                    if isinstance(p, bool):
                        judge_votes[d][j.model_id] = p
                        votes[d] = votes.get(d, 0) + (1 if p else 0)
                        present_count[d] = present_count.get(d, 0) + 1
                        if isinstance(c, float):
                            confidences[d] = confidences.get(d, 0.0) + c
                            if p:
                                supporter_conf_sum[d] = supporter_conf_sum.get(d, 0.0) + c
                    notes[d] = (notes.get(d, "") + f" | {j.model_id}: {n}").strip(" |")[:30]

                # 不再将 correctness 绑定到类别正确性；类别投票已在 judge_cls_votes 收集

            # majority vote
            yesno = {}
            conf = {}
            for d in dim_keys:
                y = votes.get(d, 0)
                total_present = present_count.get(d, 0)
                if total_present == 0:
                    yesno[d] = None
                    conf[d] = None
                else:
                    yes = y >= (total_present // 2 + 1) if total_present > 2 else y >= 1
                    yesno[d] = yes
  
                    vote_strength = (y / total_present)
                    avg_conf = (supporter_conf_sum.get(d, 0.0) / max(1, y)) if y > 0 else None
                    conf[d] = (round(vote_strength * avg_conf, 3) if avg_conf is not None else None)


            agg_label, counts, tie = majority_label(judge_cls_votes)
            class_agree = (str(it.predicted_label).lower() == agg_label.lower()) if getattr(it, "predicted_label", None) else None
            needs_review = bool(tie or (len(set(judge_cls_votes)) > 1))
            all_item_votes.append(judge_cls_votes[:])

            self.repo.upsert_aggregate(
                db, req.run_id, it.id,
                yesno=yesno, confidence=conf, notes=notes, judge_votes=judge_votes, time_ms=0.0,
                agg_label=agg_label, class_agreement=class_agree, needs_review=needs_review
            )

        # compute summary
        acc_numer = 0
        acc_denom = max(1, len(items))
        pass_rates = {k: 0 for k in dim_keys}
        for it in items:
            # not super efficient but simple; you can optimize with a join
            aggs = self.repo.list_judgments_for_item(db, req.run_id, it.id)  # we only need correctness here in real code
            # use aggregate table for correctness (already stored)
        # quick aggregate using aggregates table via list_results page 1 with large page_size
        pairs, total = self.repo.list_results(db, req.run_id, page=1, page_size=acc_denom)
        for item, agg in pairs:
            if getattr(agg, "class_agreement", None):
                acc_numer += 1
            for d in dim_keys:
                pass_rates[d] += 1 if agg.yesno.get(d) else 0


        ds_labels: List[str] | None = None
        try:
            ds_labels = dawid_skene_binary(all_item_votes, priors=anchor_priors) if all_item_votes else None
        except Exception:
            ds_labels = None


        fleiss = fleiss_kappa(all_item_votes) if all_item_votes else None
        pair_cohen: Dict[str, float] = {}
        if all_item_votes:
            cols = list(zip(*all_item_votes))
            if len(cols) >= 2:
                pair_cohen["12"] = cohens_kappa(list(cols[0]), list(cols[1]))
            if len(cols) >= 3:
                pair_cohen["13"] = cohens_kappa(list(cols[0]), list(cols[2]))
                pair_cohen["23"] = cohens_kappa(list(cols[1]), list(cols[2]))
        
        ds_diff_rate = None
        if ds_labels is not None:
            pairs2, _ = self.repo.list_results(db, req.run_id, page=1, page_size=acc_denom)
            maj = [str(agg.agg_label) for _, agg in pairs2]
            ds_diff = sum(1 for a, b in zip(maj, ds_labels) if a != b)
            ds_diff_rate = round(ds_diff / max(1, len(maj)), 4)

            for i, (item, agg) in enumerate(pairs2):
                if i < len(ds_labels) and str(agg.agg_label) != ds_labels[i]:
                    self.repo.upsert_aggregate(
                        db, req.run_id, agg.item_pk,
                        yesno=agg.yesno, confidence=agg.confidence, notes=agg.notes, judge_votes=agg.judge_votes, time_ms=agg.time_ms,
                        agg_label=agg.agg_label, class_agreement=agg.class_agreement, needs_review=True
                    )

        anchor_stats = {
            "ambiguous_seed": sum(1 for p in anchor_priors if p == "ambiguous"),
            "unambiguous_seed": sum(1 for p in anchor_priors if p == "unambiguous"),
            "none": sum(1 for p in anchor_priors if p is None),
        }

        summary = {
            "pca_agreement_rate": round(acc_numer / acc_denom, 4),
            "pass_rate": {d: round(pass_rates[d] / acc_denom, 4) for d in dim_keys},
            "items": acc_denom,
            "judges": [j for j in req.judge_models],
            "elapsed_ms": round((time.time()-t0)*1000, 1),
            "reliability": {
                "fleiss_kappa_overall": round(fleiss, 4) if fleiss is not None else None,
                "cohen_kappa_pairs": {k: round(v, 4) for k, v in pair_cohen.items()} if pair_cohen else {},
            },
            "anchors": anchor_stats,
            "ds_em": {"enabled": bool(ds_labels is not None), "diff_rate_vs_majority": ds_diff_rate}
        }
        self.repo.finish_run(db, req.run_id, summary)
        return summary

    # ---------- RESULTS ----------
    def list_results(self, db: Session, run_id: str, page: int, page_size: int):
        pairs, total = self.repo.list_results(db, run_id, page, page_size)
        rows = []
        for item, agg in pairs:
            rows.append({
                "item_id": item.item_id,
                "sentence": item.sentence,
                "gold_label": item.gold_label,
                "predicted_label": item.predicted_label,
                "rationale": item.rationale,
                "aggregate": agg.yesno,
                "confidence": agg.confidence,
                "votes": agg.judge_votes,
                "notes": agg.notes,
            })
        return {"total": total, "page": page, "page_size": page_size, "items": rows}

    # ---------- DASHBOARD ----------
    def dashboard(self, db: Session, run_id: str, page: int=1, page_size: int=12):
        return self.list_results(db, run_id, page, page_size)

    # ---------- EXPORT ----------
    def export_csv(self, db: Session, run_id: str) -> bytes:
        # pack results into a DataFrame
        pairs, total = self.repo.list_results(db, run_id, page=1, page_size=10**9)
        recs = []
        for item, agg in pairs:
            base = {
                "item_id": item.item_id,
                "sentence": item.sentence,
                "gold_label": item.gold_label,
                "predicted_label": item.predicted_label,
                "rationale": item.rationale,
            }
            # flatten aggregate yes/no
            for k, v in agg.yesno.items():
                base[f"agg_{k}"] = v
            for k, v in agg.confidence.items():
                base[f"conf_{k}"] = v
            recs.append(base)
        df = pd.DataFrame.from_records(recs)
        return df.to_csv(index=False).encode("utf-8")
