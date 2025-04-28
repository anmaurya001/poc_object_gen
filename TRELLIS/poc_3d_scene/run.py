import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
print(f"Project root: {project_root}")
sys.path.append(str(project_root))

from interface import SceneGeneratorInterface


def main():
    """Main entry point for the 3D Scene Generator application."""
    interface = SceneGeneratorInterface()
    interface.launch()


if __name__ == "__main__":
    main()
