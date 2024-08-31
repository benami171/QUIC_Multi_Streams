import unittest
import subprocess
import difflib
import os

FILE1 = "random_data_file.txt"
NUM_OF_FILES = 3

class MyTestCase(unittest.TestCase):

    def setUp(self):
        """
        Ensure the environment is clean before running tests.
        """
        self.cleanup_files()

    def cleanup_files(self):
        for i in range(1, NUM_OF_FILES + 1):
            try:
                os.remove(f"output_f{i}.txt")
            except OSError:
                pass

    def run_receiver(self):
        subprocess.run(["python", "receiver.py"], check=True)

    def run_sender(self):
        subprocess.run(["python", "sender.py"], check=True)

    def compare_files(self):
        with open(FILE1, "r", encoding="utf-8") as original_file:
            original_content = original_file.readlines()
            for i in range(1, NUM_OF_FILES + 1):
                with open(f"output_f{i}.txt", "r", encoding="utf-8") as output_file:
                    output_content = output_file.readlines()
                    diff = difflib.unified_diff(
                        original_content,
                        output_content,
                        fromfile=FILE1,
                        tofile=f"output_f{i}.txt",
                    )

                    if list(diff):
                        raise AssertionError(f"output_f{i}.txt is different from {FILE1}")

    def test_run_and_compare(self):
        self.run_receiver()
        self.run_sender()
        self.compare_files()

    def tearDown(self):
        """
        Clean up files after running tests.
        """
        self.cleanup_files()

if __name__ == '__main__':
    unittest.main()
