module.exports = {
    apps: [
      {
        name: 'iot-shadow-app',
        script: 'app.py',
        interpreter: '/usr/bin/python3',  // Use system Python3 or adjust to your venv path
        cwd: '/home/pi/innocule/aws-iot-client-py',  // Adjust to your project path
        instances: 1,
        autorestart: true,
        watch: false,
        max_memory_restart: '512M',
        env: {
          FLASK_PORT: 5000,
          FLASK_HOST: '0.0.0.0',
          FLASK_DEBUG: 'false'
        },
        log_date_format: 'YYYY-MM-DD HH:mm:ss',
        error_file: '/var/log/pm2/iot-shadow-app-error.log',
        out_file: '/var/log/pm2/iot-shadow-app-out.log',
        log_file: '/var/log/pm2/iot-shadow-app.log',
        time: true
      },
      {
        name: 'aws-iot-client-legacy',
        script: 'iot_device_controller.py',
        interpreter: '/usr/bin/python3',
        cwd: '/home/pi/innocule/aws-iot-client-py',
        instances: 1,
        autorestart: true,
        watch: false,
        max_memory_restart: '256M',
        env: {
          NODE_ENV: 'production'
        },
        disabled: true  // Disabled by default since we're using the Flask app
      }
    ]
  }
