import subprocess


def convert_backslashes(s):
    return s.encode("unicode_escape").decode()


s = r"C:\Users\axis\Downloads"
converted_s = convert_backslashes(s)
print(converted_s)  # Output: C:\\Users\\axis\\Downloads

result = subprocess.run(
    ["ls"], cwd="D:/d/p", capture_output=True, text=True, shell=True
)
print(result.stdout)
