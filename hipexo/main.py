from tmotor_control.mit_can import TMotorInterface
from hipexo.controller import ControlLoop

def main():
    motor = TMotorInterface()
    controller = ControlLoop(motor)
    controller.run()

if __name__ == '__main__':
    main()
