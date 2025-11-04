import os
import time
import threading
import asyncio

_TPM_8B = int(os.getenv("GROQ_TPM_8B", os.getenv("GROQ_TPM_LIMIT", "6000")))
_TPM_70B = int(os.getenv("GROQ_TPM_70B", os.getenv("GROQ_TPM_LIMIT_70B", "6000")))
_CONC_8B = int(os.getenv("GROQ_8B_CONCURRENCY", "4"))
_CONC_70B = int(os.getenv("GROQ_70B_CONCURRENCY", "1"))

class TokenBucket:
    def __init__(self, capacity_per_minute: int):
        self.capacity = max(1, capacity_per_minute)
        self.tokens = float(self.capacity)
        self.rate_per_sec = self.capacity / 60.0
        self.last = time.time()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.time()
        elapsed = max(0.0, now - self.last)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)
        self.last = now

    def acquire(self, required_tokens: float):
        required = max(0.0, float(required_tokens))
        while True:
            with self.lock:
                self._refill()
                if self.tokens >= required:
                    self.tokens -= required
                    return
                deficit = required - self.tokens
                wait_s = deficit / self.rate_per_sec if self.rate_per_sec > 0 else 1.0
            time.sleep(min(max(wait_s, 0.01), 2.0))

    async def acquire_async(self, required_tokens: float):
        required = max(0.0, float(required_tokens))
        while True:
            with self.lock:
                self._refill()
                if self.tokens >= required:
                    self.tokens -= required
                    return
                deficit = required - self.tokens
                wait_s = deficit / self.rate_per_sec if self.rate_per_sec > 0 else 1.0
            await asyncio.sleep(min(max(wait_s, 0.01), 2.0))


# Buckets per model
_BUCKETS = {
    "llama-3.1-8b-instant": TokenBucket(_TPM_8B),
    "llama-3.3-70b-versatile": TokenBucket(_TPM_70B),
}

# Concurrency gates (sync and async)
_SEMS = {
    "llama-3.1-8b-instant": threading.Semaphore(max(1, _CONC_8B)),
    "llama-3.3-70b-versatile": threading.Semaphore(max(1, _CONC_70B)),
}
_ASEMS = {
    "llama-3.1-8b-instant": asyncio.Semaphore(max(1, _CONC_8B)),
    "llama-3.3-70b-versatile": asyncio.Semaphore(max(1, _CONC_70B)),
}


def estimate_tokens_from_text(text: str, max_output: int = 0, extra: int = 32) -> int:
    if not isinstance(text, str):
        text = str(text)
    # Roughly ~4 chars per token
    in_tokens = max(0, int(len(text) / 4))
    return in_tokens + int(max_output) + int(extra)


def acquire_capacity(model_short: str, required_tokens: float):
    bucket = _BUCKETS.get(model_short)
    if not bucket:
        # Fallback: create with reasonable default
        bucket = TokenBucket(_TPM_8B)
        _BUCKETS[model_short] = bucket
    bucket.acquire(required_tokens)


async def acquire_capacity_async(model_short: str, required_tokens: float):
    bucket = _BUCKETS.get(model_short)
    if not bucket:
        bucket = TokenBucket(_TPM_8B)
        _BUCKETS[model_short] = bucket
    await bucket.acquire_async(required_tokens)


def enter_concurrency(model_short: str):
    sem = _SEMS.get(model_short)
    if sem is None:
        sem = threading.Semaphore(1)
        _SEMS[model_short] = sem
    return _SyncSemContext(sem)


class _SyncSemContext:
    def __init__(self, sem: threading.Semaphore):
        self.sem = sem
    def __enter__(self):
        self.sem.acquire()
    def __exit__(self, exc_type, exc, tb):
        try:
            self.sem.release()
        except Exception:
            pass


class AsyncSemContext:
    def __init__(self, asem: asyncio.Semaphore):
        self.asem = asem
    async def __aenter__(self):
        await self.asem.acquire()
        return self
    async def __aexit__(self, exc_type, exc, tb):
        try:
            self.asem.release()
        except Exception:
            pass


def get_async_sem(model_short: str) -> AsyncSemContext:
    asem = _ASEMS.get(model_short)
    if asem is None:
        asem = asyncio.Semaphore(1)
        _ASEMS[model_short] = asem
    return AsyncSemContext(asem)