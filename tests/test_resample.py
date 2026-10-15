"""common.py の単体テスト（LeRobot / ROS 不要）。  pixi run test"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import make_target_times, reorder_by_name, sample_and_hold  # noqa: E402


def test_sample_and_hold():
    times = np.array([0, 100, 250])
    values = np.array([[1.0], [2.0], [3.0]])
    out = sample_and_hold(times, values, np.array([0, 99, 100, 200, 250, 300]))
    assert out.flatten().tolist() == [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]
    # 先頭より前の時刻は最初の値
    assert sample_and_hold(times, values, np.array([-5])).flatten().tolist() == [1.0]


def test_reorder_by_name():
    names = ["b", "a", "c"]
    vals = [2.0, 1.0, 3.0]
    assert reorder_by_name(names, vals, ["a", "b", "c"]) == [1.0, 2.0, 3.0]
    assert reorder_by_name(names, vals, ["a", "x"]) == [1.0, 0.0]  # 無い関節は default
    assert reorder_by_name([], [1.0, 2.0], ["a", "b", "c"]) == [1.0, 2.0, 0.0]


def test_make_target_times():
    t = make_target_times(0, int(1e9), 20)  # 1秒 @20Hz
    assert len(t) == 20
    assert np.allclose(np.diff(t), 5e7)  # 50ms 間隔


if __name__ == "__main__":
    test_sample_and_hold()
    test_reorder_by_name()
    test_make_target_times()
    print("all tests passed")
