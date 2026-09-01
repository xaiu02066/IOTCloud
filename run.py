"""项目启动入口。

本地开发：python run.py
生产环境：gunicorn "run:app"
"""
import os

from app import create_app

config_name = os.getenv("FLASK_CONFIG", "development")
app = create_app(config_name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
