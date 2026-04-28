"""
Provider Tool Mappings

This module contains the hardcoded mappings from tool_id to tool implementations.
Separated from tool_service.py to reduce import explosion and improve maintainability.

To add a new provider tool:
1. Import the tool function at the top of this file
2. Add entry to IMAGE_PROVIDER_TOOLS or VIDEO_PROVIDER_TOOLS dict
3. The tool will be automatically registered when its provider is configured
"""

from typing import Dict, Any

# Image Generation Tools by Provider
IMAGE_PROVIDER_TOOLS: Dict[str, Dict[str, Any]] = {
    # Ideogram
    "generate_image_by_ideogram": {
        "display_name": "Ideogram",
        "type": "image",
        "provider": "ideogram",
    },
    # Nano Banana
    "generate_image_by_nano_banana": {
        "display_name": "Nano Banana",
        "type": "image",
        "provider": "nano_banana",
    },
    # Volces (Doubao)
    "generate_image_by_doubao_seedream_3_volces": {
        "display_name": "Doubao Seedream 3 by volces",
        "type": "image",
        "provider": "volces",
    },
    "edit_image_by_doubao_seededit_3_volces": {
        "display_name": "Doubao Seededit 3 by volces",
        "type": "image",
        "provider": "volces",
    },
    # Replicate Providers
    "generate_image_by_imagen_4_replicate": {
        "display_name": "Imagen 4",
        "type": "image",
        "provider": "replicate",
    },
    "generate_image_by_recraft_v3_replicate": {
        "display_name": "Recraft v3",
        "type": "image",
        "provider": "replicate",
    },
    "generate_image_by_flux_kontext_pro_replicate": {
        "display_name": "Flux Kontext Pro",
        "type": "image",
        "provider": "replicate",
    },
    "generate_image_by_flux_kontext_max_replicate": {
        "display_name": "Flux Kontext Max",
        "type": "image",
        "provider": "replicate",
    },
}

# Video Generation Tools by Provider
VIDEO_PROVIDER_TOOLS: Dict[str, Dict[str, Any]] = {
    # Volces (Doubao)
    "generate_video_by_seedance_v1_pro_volces": {
        "display_name": "Doubao Seedance v1 by volces",
        "type": "video",
        "provider": "volces",
    },
    "generate_video_by_seedance_v1_lite_volces_t2v": {
        "display_name": "Doubao Seedance v1 lite (text-to-video)",
        "type": "video",
        "provider": "volces",
    },
    "generate_video_by_seedance_v1_lite_i2v_volces": {
        "display_name": "Doubao Seedance v1 lite (images-to-video)",
        "type": "video",
        "provider": "volces",
    },
}

# Combined provider tools mapping
PROVIDER_TOOLS: Dict[str, Dict[str, Any]] = {
    **IMAGE_PROVIDER_TOOLS,
    **VIDEO_PROVIDER_TOOLS,
}


# Tool function imports - lazy loaded to avoid import explosion
# These are imported by tool_service.py when needed
def get_tool_function(tool_id: str):
    """
    Lazily import and return the tool function for a given tool_id.
    This avoids importing all tool functions at module load time.
    """
    # Image tools
    if tool_id == "generate_image_by_ideogram":
        from agents.tools.generate_image_by_ideogram import generate_image_by_ideogram
        return generate_image_by_ideogram
    elif tool_id == "generate_image_by_nano_banana":
        from agents.tools.generate_image_by_nano_banana import generate_image_by_nano_banana
        return generate_image_by_nano_banana
    elif tool_id == "generate_image_by_doubao_seedream_3_volces":
        from agents.tools.generate_image_by_doubao_seedream_3_volces import generate_image_by_doubao_seedream_3_volces
        return generate_image_by_doubao_seedream_3_volces
    elif tool_id == "edit_image_by_doubao_seededit_3_volces":
        from agents.tools.generate_image_by_doubao_seededit_3_volces import edit_image_by_doubao_seededit_3_volces
        return edit_image_by_doubao_seededit_3_volces
    elif tool_id == "generate_image_by_imagen_4_replicate":
        from agents.tools.generate_image_by_imagen_4_replicate import generate_image_by_imagen_4_replicate
        return generate_image_by_imagen_4_replicate
    elif tool_id == "generate_image_by_recraft_v3_replicate":
        from agents.tools.generate_image_by_recraft_v3_replicate import generate_image_by_recraft_v3_replicate
        return generate_image_by_recraft_v3_replicate
    elif tool_id == "generate_image_by_flux_kontext_pro_replicate":
        from agents.tools.generate_image_by_flux_kontext_pro_replicate import generate_image_by_flux_kontext_pro_replicate
        return generate_image_by_flux_kontext_pro_replicate
    elif tool_id == "generate_image_by_flux_kontext_max_replicate":
        from agents.tools.generate_image_by_flux_kontext_max_replicate import generate_image_by_flux_kontext_max_replicate
        return generate_image_by_flux_kontext_max_replicate
    # Video tools
    elif tool_id == "generate_video_by_seedance_v1_pro_volces":
        from agents.tools.generate_video_by_seedance_v1_pro_volces import generate_video_by_seedance_v1_pro_volces
        return generate_video_by_seedance_v1_pro_volces
    elif tool_id == "generate_video_by_seedance_v1_lite_volces_t2v":
        from agents.tools.generate_video_by_seedance_v1_lite_volces import generate_video_by_seedance_v1_lite_t2v
        return generate_video_by_seedance_v1_lite_t2v
    elif tool_id == "generate_video_by_seedance_v1_lite_i2v_volces":
        from agents.tools.generate_video_by_seedance_v1_lite_volces import generate_video_by_seedance_v1_lite_i2v
        return generate_video_by_seedance_v1_lite_i2v
    else:
        raise ValueError(f"Unknown tool_id: {tool_id}")


def get_provider_for_tool(tool_id: str) -> str | None:
    """Get the provider name for a given tool_id."""
    return PROVIDER_TOOLS.get(tool_id, {}).get("provider")


def get_tool_type(tool_id: str) -> str | None:
    """Get the tool type (image/video) for a given tool_id."""
    return PROVIDER_TOOLS.get(tool_id, {}).get("type")


def get_all_tool_ids() -> list:
    """Get list of all available tool IDs."""
    return list(PROVIDER_TOOLS.keys())
