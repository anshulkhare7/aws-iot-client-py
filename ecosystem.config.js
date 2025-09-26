module.exports = {
    apps: [{
      name: 'aws-iot-client',
      script: 'iot_device_controller.py',
      interpreter: '/home/pi/innocule/aws-iot-client-py/aws-iot/bin/python',  // Adjust pathto your venv
      cwd: '/home/pi/innocule/aws-iot-client-py',         // Adjust to yourproject path
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    }]
  }
