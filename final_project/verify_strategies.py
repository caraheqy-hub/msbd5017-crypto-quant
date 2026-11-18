"""复核当前三个案例；完整检查逻辑统一使用 build_cases，避免多套口径。"""
from build_cases import CASES, build

if __name__ == "__main__":
    for name, label in CASES:
        build(name, label)
