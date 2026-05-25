import unittest

from controllers.robot_controller import RobotController
from utils.security import SecurityError


class RobotControllerTests(unittest.TestCase):
    def test_cartesian_target_generates_safe_angles(self):
        controller = RobotController()
        angles = controller.cartesian_to_servo_angles(140, 0, 80)

        self.assertEqual(len(angles), 5)
        self.assertTrue(all(0 <= angle <= 180 for angle in angles))

    def test_send_angles_is_simulated_by_default(self):
        controller = RobotController()
        result = controller.send_angles([90, 90, 90, 90, 90])

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["simulated"])
        self.assertEqual(result["serial_command"], "MOVE,90,90,90,90,90")

    def test_emergency_blocks_motion_until_cleared(self):
        controller = RobotController()
        controller.emergency_stop("test")

        with self.assertRaises(SecurityError):
            controller.send_angles([90, 90, 90, 90, 90])

        controller.clear_emergency()
        self.assertEqual(controller.send_angles([90, 90, 90, 90, 90])["status"], "success")


if __name__ == "__main__":
    unittest.main()
