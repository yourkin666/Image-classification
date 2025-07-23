module.exports = {
  apps: [
    {
      name: "image-classification-api",
      script: "/root/Image-classification/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 5000",
      cwd: "/root/Image-classification",
      interpreter: "/root/Image-classification/venv/bin/python",
      env: {
        NODE_ENV: "production",
      },
      watch: false,
      instances: 1,
      exec_mode: "fork",
      max_memory_restart: "500M",
      restart_delay: 3000,
      autorestart: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      error_file: "/root/Image-classification/logs/error.log",
      out_file: "/root/Image-classification/logs/out.log"
    }
  ]
}
