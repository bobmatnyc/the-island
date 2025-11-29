module.exports = {
  apps: [
    {
      name: 'epstein-backend',
      script: '.venv/bin/python3',
      args: '-m uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload',
      cwd: '/Users/masa/Projects/epstein',
      interpreter: 'none',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      env: {
        PYTHONUNBUFFERED: '1',
        // ChromaDB telemetry settings (both cases to ensure coverage)
        anonymized_telemetry: 'false',
        ANONYMIZED_TELEMETRY: 'false',
        chroma_telemetry_impl: 'none',
        CHROMA_TELEMETRY_IMPL: 'none',
        // Disable LLM classification to avoid blocking API calls
        ENABLE_LLM_CLASSIFICATION: 'false'
      }
    },
    {
      name: 'epstein-frontend',
      script: 'npm',
      args: 'run dev',
      cwd: '/Users/masa/Projects/epstein/frontend',
      interpreter: 'none',
      watch: false,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    }
  ]
};
