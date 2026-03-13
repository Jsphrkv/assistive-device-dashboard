import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 5000 locally, Render overrides
    app.run(host="0.0.0.0", port=port)

print(f">>> Starting on PORT: {os.environ.get('PORT', 'NOT SET')}")

try:
    app = create_app()
    print(">>> App created successfully")
except Exception as e:
    print(f">>> FAILED to create app: {e}")
    raise