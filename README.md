# James - PneumatCraft AI Design System

James is an AI-powered design system for pneumatic structures (气模). It generates professional design prompts through multi-candidate enhancement and scoring.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Input                              │
│              (e.g., "生成一个卡通风格的红色大气模")              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              enhance_airmold_prompt                         │
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
│              enhance_airmold_prompt                         │
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
│              check_airmold_image (VQA)                      │
│         (Verify image matches prompt)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (if errors)
┌─────────────────────────────────────────────────────────────┐
│              refine_airmold_prompt                          │
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
- **Tool integration**: enhance_airmold_prompt, score_airmold_prompt, check_airmold_image, refine_airmold_prompt

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
│   │   └── enhance_airmold_prompt.py
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
python main.py
```

### Frontend

```bash
cd react
npm install
npm run dev
```

## API Configuration

Edit `server/tools/jaaz/` to configure API providers:

- **Gemini**: Primary LLM for prompt enhancement
- **MiniMax**: Alternative provider
- **ComfyUI**: Local image generation (optional)

## Development

```bash
# Start backend
cd server && python main.py --port 57988

# Start frontend (separate terminal)
cd react && npm run dev
```

## License

MIT
