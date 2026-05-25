# CHEVEL 5DOF Arm Bridge

CHEVEL includes a safe first bridge for a 5-servo Arduino Mega 2560 arm. The Python controller runs in simulation by default and only writes to hardware when a serial port is explicitly configured.

## Hardware Target

- Board: Arduino Mega 2560.
- Servos: MG996R for high-load joints, SG90 for wrist/gripper.
- Channels:
  - servo 0: base, pin 2;
  - servo 1: shoulder, pin 3;
  - servo 2: elbow, pin 4;
  - servo 3: wrist, pin 5;
  - servo 4: gripper, pin 6.

Do not power MG996R motors from the Arduino 5V pin. Use an external regulated servo supply and a shared ground.

## Serial Protocol

Baud rate: `115200`.

```text
PING
STATUS
LIMITS
HOME
ARM
STOP
SET,index,angle
MOVE,base,shoulder,elbow,wrist,gripper
```

`STOP` detaches servos in firmware. `ARM` attaches them again after a human safety check.

## Python Controller

`controllers.robot_controller.RobotController` provides:

- cartesian-to-servo conversion for a 5DOF hobby arm;
- optional IKPy inverse-kinematics backend when `requirements-hardware.txt` is installed;
- deterministic analytical IK fallback when IKPy is unavailable;
- servo limit validation before every output;
- emergency stop state;
- simulation mode by default;
- optional serial bridge through `pyserial`.

Example:

```python
from controllers.robot_controller import RobotController

arm = RobotController()
print(arm.move_cartesian(140, 0, 80))
print(arm.emergency_stop("human_check"))
```

For real hardware:

```python
arm = RobotController(port="COM5", simulate=False)
arm.home()
```

## Safety

All outgoing angles are checked through `utils.security.validate_servo_angles`. Cartesian targets are checked through `validate_cartesian_workspace`. CHEVEL also runs fast reflex rules in `core.fast_thinking` so critical signals such as a person in the arm zone or battery below 10 percent produce an emergency stop reflex before LLM reasoning.

For hardware extras:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-hardware.txt
```
