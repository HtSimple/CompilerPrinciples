# src/test_driver.py
# --------------------------------------------
# 测试生成的编译器
# 可以批量运行多个测试源程序，验证生成的 TAC 是否正确
# --------------------------------------------

import os
from main import compile_source_file

TEST_DIR = "test/"
TAC_OUTPUT_DIR = "generated_compiler/tac_test_outputs/"

def run_all_tests():
    if not os.path.exists(TAC_OUTPUT_DIR):
        os.makedirs(TAC_OUTPUT_DIR)

    test_files = [f for f in os.listdir(TEST_DIR) if f.endswith(".pl0") or f.endswith(".decaf")]

    for test_file in test_files:
        source_path = os.path.join(TEST_DIR, test_file)
        tac_output_path = os.path.join(TAC_OUTPUT_DIR, test_file + ".tac")
        print(f"\n[TEST] Compiling {test_file} ...")
        try:
            compile_source_file(source_path, tac_output_path)
            print(f"[PASS] {test_file} compiled successfully.")
        except Exception as e:
            print(f"[FAIL] {test_file} failed: {e}")


if __name__ == "__main__":
    run_all_tests()