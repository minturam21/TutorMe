
import unittest

from models.visual_action import VisualAction


class VisualActionTests(unittest.TestCase):

    def test_valid_action(self):
        action = VisualAction(
            id="action_1",
            type="draw_shape",
            target_id="circle_1",
            parameters={
                "shape": "circle",
                "x": 100,
                "y": 100,
                "width": 60,
                "height": 60,
            },
            duration=1,
            easing="ease_in_out",
            order=0,
        )

        self.assertEqual(action.type, "draw_shape")

    def test_invalid_action_type(self):
        with self.assertRaises(ValueError):
            VisualAction(
                id="action_2",
                type="make_magic",
                order=0,
            )

    def test_negative_duration(self):
        with self.assertRaises(ValueError):
            VisualAction(
                id="action_3",
                type="wait",
                duration=-1,
                order=0,
            )


    def test_reject_path_point_outside_canvas(self):
        with self.assertRaises(ValueError):
            VisualAction(
                id="action_path",
                type="draw_path",
                target_id="path_1",
                parameters={
                    "points": [[100, 100], [2100, 200]],
                },
                order=0,
            )

    def test_reject_shape_exceeding_canvas(self):
        with self.assertRaises(ValueError):
            VisualAction(
                id="action_shape",
                type="draw_shape",
                target_id="shape_1",
                parameters={
                    "shape": "rectangle",
                    "x": 1950,
                    "y": 100,
                    "width": 100,
                    "height": 50,
                },
                order=0,
            )

    def test_accept_valid_path(self):
        action = VisualAction(
            id="action_valid_path",
            type="draw_path",
            target_id="path_1",
            parameters={
                "points": [[100, 100], [500, 400]],
            },
            order=0,
        )

        self.assertEqual(action.type, "draw_path")


if __name__ == "__main__":
    unittest.main()
