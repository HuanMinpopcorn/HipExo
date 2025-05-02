# Hipexo Project

This project controls exoskeleton hardware using `TmotorCANControl`.

# To Set Up the Environment
1. Install the required packages:
   ```bash
   pip install -e .
   ```
2. Install the edited `TmotorCANControl` package:
   ```bash
    git clone https://github.com/HuanMinpopcorn/TMotorCANControl.git
   ```


# To Run the Code
* step 1 . connect the hardware and run the can0 in readme at demo folder
    ```bash
    sudo ip link set can0 up type can bitrate 1000000
    sudo ip link set can0 up
    ```
* step 2 . check the connection for motor and sensor 
    * step 2.1 check the connection of motor
        ```bash
            python3 ./script/check_motor_connection_mit_can.py.py
        ```
    * step 2.2 check the connection of load cell 
        ```bash
            python3 ./script/check_load_cell_connection.py
        ```
* step 3 . write the admittance control 
    * initialize the motor position and tare/calibrate load cell reading 
    * read 10 position and 10 velocity in 1khz at t and t+1 to get theta_dot and theta ddot 
    * read torque from load cell in 1khz 

