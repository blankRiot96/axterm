from pathlib import Path

test = """

Path
----
D:\\d\\p\\axterm

"""

stripped = test.strip()
lines = stripped.splitlines()
line = lines[-1].replace("\\", "/")
path = bytes(line, "ascii").decode("unicode-escape")
test = Path(path)
print(test)
