import httpx
import uuid
import json

SERVER_URL = "http://127.0.0.1:57988"

def test_repro():
    session_id = f"repro_session_{uuid.uuid4().hex[:8]}"
    canvas_id = f"repro_canvas_{uuid.uuid4().hex[:8]}"
    
    payload = {
        "messages": [
            {"role": "user", "content": "设计一款万圣节充气装饰，美国家庭使用场景，涤塔夫材质"}
        ],
        "session_id": session_id,
        "canvas_id": canvas_id,
        "text_model": {
            "model": "gemini-2.5-pro",
            "provider": "gemini",
            "url": "https://generativelanguage.googleapis.com/"
        },
        "tool_list": [
            {
                "id": "generate_image_by_ideogram",
                "provider": "ideogram",
                "type": "image",
                "display_name": "Ideogram"
            }
        ]
    }
    
    print(f"Sending request to {SERVER_URL}/api/chat...")
    try:
        response = httpx.post(
            f"{SERVER_URL}/api/chat",
            json=payload,
            headers={"Authorization": "Bearer test_token"},
            timeout=120
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_repro()
