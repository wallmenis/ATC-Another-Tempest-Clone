import os
import sys

if not os.path.isdir("gameEnv"):
        os.system("python -m venv gameEnv")
        if sys.platform == "win32":
            os.system(
                "gameEnv\\bin\\python -m pip install -r requirements.txt"
            )  # reminder to use os.path next time
            os.system("gameEnv\\bin\\python Game.py")
        else:
            os.system("gameEnv/bin/python -m pip install -r requirements.txt")
            os.system("gameEnv/bin/python Game.py")
        exit()
if sys.platform == "win32":
    os.system("gameEnv\\bin\\python Game.py")
else:
    os.system("gameEnv/bin/python Game.py")
exit()
