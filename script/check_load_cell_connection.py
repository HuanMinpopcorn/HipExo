import serial

# Set up the serial connection
ser = serial.Serial(
    port='/dev/ttyUSB0',     # Adjust based on your device
    baudrate=9600,         # Match the device's baud rate
    timeout=1                # Timeout in seconds for read()
)

print(f"Opened serial port: {ser.name}")

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            print(f"Received: {line}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
