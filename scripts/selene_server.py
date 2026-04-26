#!/usr/bin/env python3
import os
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

MODEL_PATH = os.path.expanduser("~/.cache/huggingface/hub/models--AtlaAI--Selene-1-Mini-Llama-3.1-8B/snapshots/427792f1c3e2073cb7da216924fd884b1ba496e0")

app = FastAPI(title="Selene LLM Server")
model = None
tokenizer = None


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


@app.on_event("startup")
def load_model():
    global model, tokenizer
    print(f"Loading model from {MODEL_PATH}...")

    from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaConfig

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Using device: {device}")

    config = LlamaConfig.from_pretrained(MODEL_PATH)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

    if device == "mps":
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            config=config,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            config=config,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
    print("Model loaded successfully!")


@app.get("/health")
def health():
    return {"status": "ok", "model": "Selene-1-Mini-Llama-3.1-8B"}


@app.post("/v1/completions")
def completions(req: CompletionRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    inputs = tokenizer(req.prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        do_sample=True
    )
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"choices": [{"text": result[len(req.prompt):]}]}


@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    prompt = ""
    for msg in req.messages:
        if msg.role == "system":
            prompt += f"System: {msg.content}\n"
        elif msg.role == "user":
            prompt += f"User: {msg.content}\n"
        else:
            prompt += f"Assistant: {msg.content}\n"
    prompt += "Assistant:"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=req.max_tokens,
        temperature=req.temperature,
        do_sample=True
    )
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = result[len(prompt):].strip()
    return {"choices": [{"message": {"role": "assistant", "content": response}}]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)