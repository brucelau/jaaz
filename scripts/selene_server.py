#!/usr/bin/env python3
import os
import asyncio
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import torch.nn as nn

MODEL_PATH = os.getenv("SELENE_MODEL_PATH", os.path.expanduser("~/.cache/huggingface/hub/models--AtlaAI--Selene-1-Mini-Llama-3.1-8B/snapshots/427792f1c3e2073cb7da216924fd884b1ba496e0"))

MAX_CONCURRENT = int(os.getenv("SELENE_MAX_CONCURRENT", "4"))
MAX_QUEUE_SIZE = int(os.getenv("SELENE_MAX_QUEUE", "16"))
MAX_MEMORY_MB = int(os.getenv("SELENE_MAX_MEMORY_MB", "8192"))
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

app = FastAPI(title="Selene LLM Server")

model = None
tokenizer = None
model_loading = False
model_ready = False
_load_error: Optional[str] = None

_semaphore: asyncio.Semaphore = None
_queue: asyncio.Queue = None


class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7


def _get_mps_memory_allocated() -> float:
    if DEVICE != "mps":
        return 0.0
    try:
        return torch.mps.current_allocated_memory() / 1024 / 1024
    except Exception:
        return 0.0


def _get_mps_memory_limit() -> float:
    if DEVICE != "mps":
        return 0.0
    try:
        return torch.mps.driver_allocated_memory() / 1024 / 1024
    except Exception:
        return 0.0


def _build_max_memory() -> dict:
    if DEVICE == "cpu":
        return None
    return {DEVICE: f"{MAX_MEMORY_MB}MB"}


async def load_model_async():
    global model, tokenizer, model_loading, model_ready, _load_error
    model_loading = True
    _load_error = None

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaConfig

        print(f"[Selene] Loading model from {MODEL_PATH}...")
        print(f"[Selene] Device: {DEVICE}, max_memory: {MAX_MEMORY_MB}MB, max_concurrent: {MAX_CONCURRENT}")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

        load_kwargs = {
            "torch_dtype": torch.float16 if DEVICE == "mps" else torch.float32,
        }

        max_memory = _build_max_memory()
        if max_memory:
            load_kwargs["max_memory"] = max_memory

        if DEVICE == "mps":
            load_kwargs["device_map"] = "auto"
        else:
            load_kwargs["device_map"] = "cpu"

        config = LlamaConfig.from_pretrained(MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, config=config, **load_kwargs)

        model_ready = True
        model_loading = False
        print("[Selene] Model loaded successfully!")
    except Exception as e:
        _load_error = str(e)
        model_loading = False
        model_ready = False
        print(f"[Selene] Failed to load model: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _semaphore, _queue
    _semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    _queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

    asyncio.create_task(load_model_async())

    yield

    global model, tokenizer, model_ready
    print("[Selene] Shutting down, releasing model resources...")
    if model is not None:
        del model
        model = None
        tokenizer = None
        model_ready = False
        if DEVICE == "mps":
            torch.mps.empty_cache()
    print("[Selene] Shutdown complete.")


app = FastAPI(title="Selene LLM Server", lifespan=lifespan)


@app.get("/health")
def health():
    if model_loading:
        return {"status": "loading", "model": "Selene-1-Mini-Llama-3.1-8B"}
    if _load_error:
        return {"status": "error", "error": _load_error}
    if not model_ready or model is None:
        return {"status": "not_ready", "model": "Selene-1-Mini-Llama-3.1-8B"}
    mps_mem = _get_mps_memory_allocated() if DEVICE == "mps" else 0
    return {
        "status": "ok",
        "model": "Selene-1-Mini-Llama-3.1-8B",
        "device": DEVICE,
        "mps_memory_mb": round(mps_mem, 1),
    }


@app.get("/health/detailed")
def health_detailed():
    mps_allocated = _get_mps_memory_allocated() if DEVICE == "mps" else 0
    queue_size = _queue.qsize() if _queue else 0
    sem_used = MAX_CONCURRENT - _semaphore._value if _semaphore else 0

    return {
        "status": "ok" if model_ready else "loading",
        "model": "Selene-1-Mini-Llama-3.1-8B",
        "device": DEVICE,
        "mps_memory_mb": round(mps_allocated, 1),
        "max_memory_mb": MAX_MEMORY_MB,
        "concurrent": {"used": sem_used, "max": MAX_CONCURRENT},
        "queue": {"size": queue_size, "max": MAX_QUEUE_SIZE},
        "model_loading": model_loading,
        "model_ready": model_ready,
        "load_error": _load_error,
    }


@app.post("/v1/completions")
async def completions(req: CompletionRequest):
    if not model_ready or model is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    async with _semaphore:
        loop = asyncio.get_event_loop()
        inputs = await loop.run_in_executor(
            None, lambda: tokenizer(req.prompt, return_tensors="pt").to(model.device)
        )
        outputs = await loop.run_in_executor(
            None,
            lambda: model.generate(
                **inputs,
                max_new_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                do_sample=True
            )
        )
        result = await loop.run_in_executor(None, lambda: tokenizer.decode(outputs[0], skip_special_tokens=True))
        return {"choices": [{"text": result[len(req.prompt):]}]}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    if not model_ready or model is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    prompt = ""
    for msg in req.messages:
        if msg.role == "system":
            prompt += f"System: {msg.content}\n"
        elif msg.role == "user":
            prompt += f"User: {msg.content}\n"
        else:
            prompt += f"Assistant: {msg.content}\n"
    prompt += "Assistant:"

    async with _semaphore:
        loop = asyncio.get_event_loop()
        inputs = await loop.run_in_executor(
            None, lambda: tokenizer(prompt, return_tensors="pt").to(model.device)
        )
        outputs = await loop.run_in_executor(
            None,
            lambda: model.generate(
                **inputs,
                max_new_tokens=req.max_tokens,
                temperature=req.temperature,
                do_sample=True
            )
        )
        result = await loop.run_in_executor(None, lambda: tokenizer.decode(outputs[0], skip_special_tokens=True))
        response = result[len(prompt):].strip()
        return {"choices": [{"message": {"role": "assistant", "content": response}}]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
