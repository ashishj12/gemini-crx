import os
import uvicorn
from relay_api.core.config import load_environment

if __name__ == "__main__":
    load_environment()
    uvicorn.run(
        "relay_api.http.app:create_app",
        factory=True,
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", os.getenv("APP_PORT", "8080"))),
        access_log=False,
    )
