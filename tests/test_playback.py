import unittest
from src.playback import Playback


class PlaybackTests(unittest.TestCase):
    def test_clock_advances_then_pauses_exactly_once(self):
        clock = Playback(minutes_per_second=3)
        clock.resume(100)
        self.assertFalse(clock.tick(105))
        self.assertEqual(clock.time_label, "1:15 PM")
        self.assertTrue(clock.tick(120))
        self.assertEqual(clock.time_label, "2:00 PM")
        self.assertFalse(clock.running)
        self.assertFalse(clock.tick(999))
        self.assertEqual(clock.checkpoint, 2)

    def test_large_time_gap_never_skips_key_moments(self):
        clock = Playback(minutes_per_second=3)
        for stage, expected in enumerate(("2:00 PM", "3:00 PM", "3:30 PM", "4:00 PM"), 2):
            clock.resume(0)
            self.assertTrue(clock.tick(10000))
            self.assertEqual(clock.checkpoint, stage)
            self.assertEqual(clock.time_label, expected)
        clock.resume(20000)
        self.assertFalse(clock.running)
        self.assertTrue(clock.finished)

    def test_manual_pause_excludes_paused_wall_time(self):
        clock = Playback(minutes_per_second=3)
        clock.resume(0)
        clock.tick(5)
        clock.pause()
        clock.tick(100)
        self.assertEqual(clock.minutes, 15)
        clock.resume(200)
        clock.tick(201)
        self.assertEqual(clock.minutes, 18)

    def test_repeat_ticks_and_resume_are_idempotent(self):
        clock = Playback(minutes_per_second=3)
        clock.resume(100)
        clock.resume(101)
        clock.tick(102)
        clock.tick(102)
        clock.tick(101)
        self.assertEqual(clock.minutes, 6)
        self.assertEqual(Playback.at_stage(4).time_label, "3:30 PM")
