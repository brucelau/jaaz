# James - PneumatCraft AI Design System

James is an AI-powered design system for inflatable products (充气装饰). It generates professional design prompts through multi-candidate enhancement and scoring.

## 主要功能

- **充气装饰设计增强**：基于材质/结构/节日/风格多维度评分，自动优化 prompt
- **多模型图像生成**：Ideogram、Nano Banana、Flux、Recraft 等
- **本地用户认证**：SQLite + bcrypt，支持注册/登录/Token 刷新
- **实时流式响应**：Socket.IO WebSocket 双向通信

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Input                              │
│              (e.g., "生成一个卡通风格的红色大气模")              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              enhance_inflatable_prompt                         │
│  • Pattern Matching (matching design specs)                │
│  • LLM Enhancement (generate 3 candidates)                 │
│  • Batch Scoring (select best by 4-dimension score)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Agent: Design Strategy Doc (用户语言)               │
│  • 分辨率 / Resolution                                     │
│  • 风格与氛围 / Style & Mood                              │
│  • 关键视觉元素 / Key Visual Elements                       │
│  • 构图与布局 / Composition & Layout                       │
│  • 色彩方案 / Color Palette                                │
│  • 材质说明 / Material Description                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Agent: Generate English Prompt                     │
│           (Based on Design Strategy Doc)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    generate_image                            │
│         (Flux/ Ideogram/ ComfyUI / etc.)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              enhance_inflatable_prompt                         │
│  • Pattern Matching (matching design specs)                │
│  • LLM Enhancement (generate 3 candidates)                 │
│  • Batch Scoring (select best by 4-dimension score)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Agent: English Design Strategy Doc                 │
│              (Design rationale in English)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    generate_image                            │
│         (Flux/ Ideogram/ ComfyUI / etc.)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              check_inflatable_image (VQA)                      │
│         (Verify image matches prompt)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (if errors)
┌─────────────────────────────────────────────────────────────┐
│              refine_inflatable_prompt                          │
│           (Fix errors, regenerate)                          │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Prompt Enhancement (`server/tools/patterns/`)

| Module | Description |
|--------|-------------|
| `enhancer.py` | Generates 3 candidate prompts via LLM with pattern matching |
| `scorer.py` | Rule-based scoring on 4 dimensions |
| `matcher.py` | Matches user input against design pattern database |
| `refinement_engine.py` | Refines prompts based on error feedback |

### Scoring Dimensions

| Dimension | Keywords |
|----------|----------|
| Material Accuracy | PVC, TPU, Dacron, 防水, 耐磨 |
| Structural Soundness | 充气, 接缝, 底座, 支撑 |
| Visual Quality | 构图, 光影, 背景, 8K |
| Color Accuracy | 配色, Pantone, 色系 |

**Pass threshold**: overall >= 3.5

### Agent System (`server/services/`)

- **image_vide_creator**: Main agent for image/video generation
- **System prompts**: Defines workflow and tool usage
- **Tool integration**: enhance_inflatable_prompt, score_inflatable_prompt, check_inflatable_image, refine_inflatable_prompt

## Project Structure

```
jaaz/
├── react/                 # Frontend (React + Vite)
│   └── src/
│       ├── components/    # UI components
│       ├── pages/        # Page components
│       └── i18n/         # Internationalization
├── server/               # Backend
│   ├── tools/           # Agent tools
│   │   ├── patterns/    # Pattern matching & enhancement
│   │   └── enhance_inflatable_prompt.py
│   ├── services/        # Agent services
│   │   └── langgraph_service/
│   │       └── configs/ # Agent configurations
│   └── routers/         # API routes
└── docs/                # Documentation
```

## Setup

### Requirements
- Python >= 3.12
- Node.js >= 18
- Gemini API key (or other LLM API)

### Backend

```bash
cd server
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 57988
```

### Frontend

```bash
cd react
npm install
npm run dev
```

### 认证

首次使用需要注册本地用户：

```bash
curl -X POST http://127.0.0.1:57988/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "yourname", "email": "you@example.com", "password": "yourpassword"}'
```

登录后会返回 `local_xxx` token，在后续请求中通过 `Authorization: Bearer <token>` header 携带。

## API Configuration

Edit `server/tools/jaaz/` to configure API providers:

- **Gemini**: Primary LLM for prompt enhancement
- **MiniMax**: Alternative provider
- **ComfyUI**: Local image generation (optional)

## Development

```bash
# Start backend (from server/ directory)
cd server && /path/to/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 57988

# Start frontend (separate terminal)
cd react && npm run dev
```

## License

MIT
