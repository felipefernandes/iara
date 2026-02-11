import os
import tempfile
import unittest

from iara.scanner import scan_directory


class TestScanDirectory(unittest.TestCase):
    def test_no_relevant_stack_returns_warning(self):
        config = {"project": {"tech_stack": ["Rust"]}}
        result = scan_directory(".", config)
        self.assertIn("No relevant extensions", result)

    def test_python_stack_no_files_returns_clean(self):
        config = {"project": {"tech_stack": ["Python"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_directory(tmpdir, config)
            self.assertIn("No critical issues", result)

    def test_cs_scan_clean_file(self):
        config = {"project": {"tech_stack": ["Unity"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            cs_file = os.path.join(tmpdir, "Clean.cs")
            with open(cs_file, "w", encoding="utf-8") as f:
                f.write("using UnityEngine;\npublic class Clean {\n    void Start() { }\n}\n")

            result = scan_directory(tmpdir, config)
            self.assertIn("No critical issues", result)

    def test_cs_scan_detects_getcomponent_in_update(self):
        config = {"project": {"tech_stack": ["C#"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            cs_file = os.path.join(tmpdir, "Player.cs")
            with open(cs_file, "w", encoding="utf-8") as f:
                f.write(
                    "using UnityEngine;\n"
                    "public class Player : MonoBehaviour {\n"
                    "    void Update() {\n"
                    "        var rb = GetComponent<Rigidbody>();\n"
                    "    }\n"
                    "}\n"
                )

            result = scan_directory(tmpdir, config)
            self.assertIn("Scan Results", result)
            self.assertIn("GetComponent", result)

    def test_cs_scan_detects_find_in_update(self):
        config = {"project": {"tech_stack": ["Unity"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            cs_file = os.path.join(tmpdir, "Enemy.cs")
            with open(cs_file, "w", encoding="utf-8") as f:
                f.write(
                    "public class Enemy : MonoBehaviour {\n"
                    "    void FixedUpdate() {\n"
                    "        var go = Find(\"Player\");\n"
                    "    }\n"
                    "}\n"
                )

            result = scan_directory(tmpdir, config)
            self.assertIn("Scan Results", result)
            self.assertIn("Find", result)

    def test_cs_scan_detects_debug_log_in_update(self):
        config = {"project": {"tech_stack": ["Unity"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            cs_file = os.path.join(tmpdir, "Logger.cs")
            with open(cs_file, "w", encoding="utf-8") as f:
                f.write(
                    "public class Logger : MonoBehaviour {\n"
                    "    void LateUpdate() {\n"
                    "        Debug.Log(\"tick\");\n"
                    "    }\n"
                    "}\n"
                )

            result = scan_directory(tmpdir, config)
            self.assertIn("Scan Results", result)
            self.assertIn("Debug.Log", result)

    def test_cs_no_update_context_skips_rules(self):
        config = {"project": {"tech_stack": ["Unity"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            cs_file = os.path.join(tmpdir, "Safe.cs")
            with open(cs_file, "w", encoding="utf-8") as f:
                f.write(
                    "public class Safe : MonoBehaviour {\n"
                    "    void Start() {\n"
                    "        var rb = GetComponent<Rigidbody>();\n"
                    "        Debug.Log(\"init\");\n"
                    "    }\n"
                    "}\n"
                )

            result = scan_directory(tmpdir, config)
            self.assertIn("No critical issues", result)

    def test_scan_nested_directories(self):
        config = {"project": {"tech_stack": ["Unity"]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "Scripts", "Player")
            os.makedirs(subdir)
            cs_file = os.path.join(subdir, "Movement.cs")
            with open(cs_file, "w", encoding="utf-8") as f:
                f.write(
                    "public class Movement : MonoBehaviour {\n"
                    "    void Update() {\n"
                    "        var rb = GetComponent<Rigidbody>();\n"
                    "    }\n"
                    "}\n"
                )

            result = scan_directory(tmpdir, config)
            self.assertIn("Scan Results", result)

    def test_empty_tech_stack_returns_warning(self):
        config = {"project": {"tech_stack": []}}
        result = scan_directory(".", config)
        self.assertIn("No relevant extensions", result)

    def test_missing_project_key(self):
        config = {}
        result = scan_directory(".", config)
        self.assertIn("No relevant extensions", result)


if __name__ == "__main__":
    unittest.main()
