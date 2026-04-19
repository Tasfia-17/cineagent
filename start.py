"""
start.py — starts ShopReel server + ngrok tunnel in one command.
Run from inside ~/cineagent:  python start.py

Prints the public ngrok URL to register as Shopify webhook.
"""

import threading
import uvicorn
from pyngrok import ngrok

def run_server():
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    # Start FastAPI in background thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    import time; time.sleep(2)  # wait for server to start

    # Open ngrok tunnel
    tunnel = ngrok.connect(8000)
    public_url = tunnel.public_url

    print("\n" + "="*60)
    print("  🛍️  ShopReel is running!")
    print(f"\n  Local:  http://localhost:8000")
    print(f"  Public: {public_url}")
    print(f"\n  Shopify webhook URL:")
    print(f"  👉  {public_url}/webhook/shopify")
    print("\n  Register this URL in:")
    print("  Shopify Admin → Settings → Notifications → Webhooks")
    print("  Event: Product creation")
    print("="*60 + "\n")

    # Keep alive
    try:
        t.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
        ngrok.disconnect(public_url)
