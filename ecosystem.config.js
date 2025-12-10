module.exports = {
  apps: [
    {
      name: "evalmate_frontend",
      script: "npm",
      args: "start",
      cwd: "/home/zerone/evalmate/next_js",
      instances: 1,
      autorestart: true,
      max_restarts: 3,
      min_uptime: "30s",
      restart_delay: 3000,
      kill_timeout: 5000,
      listen_timeout: 15000,
      max_memory_restart: "250M",
      watch: false,
      ignore_watch: ["node_modules", ".next"],
      error_file: "/home/zerone/.pm2/logs/evalmate-frontend-error.log",
      out_file: "/home/zerone/.pm2/logs/evalmate-frontend-out.log",
      merge_logs: true,
      env: {
        NODE_ENV: "production",
        PORT: 3000,
        NEXT_PUBLIC_API_URL: "http://167.71.133.166:8000",
      },
    },
  ],
};
