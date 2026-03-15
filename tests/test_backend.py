import requests
import json

def test_root():
    response = requests.get("http://localhost:8000/")
    assert response.status_code == 200
    assert response.json()["status"] == "Riverwood AI Server Online"

def test_chat():
    payload = {
        "user_input": "Namaste! What is the update for Sector A?",
        "session_id": "test_session"
    }
    response = requests.post("http://localhost:8000/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "audio_url" in data
    print(f"AI Response: {data['response']}")

if __name__ == "__main__":
    # Note: Backend must be running for these tests to pass
    try:
        test_root()
        print("Root test passed!")
        test_chat()
        print("Chat test passed!")
    except Exception as e:
        print(f"Tests failed: {e}")
