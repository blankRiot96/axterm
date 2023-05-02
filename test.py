import subprocess

# Ask the user to enter a command
command = "py"

# Use subprocess to execute the command and capture the output
output = subprocess.check_output(command, shell=True, universal_newlines=True)

# Print the output
print(output)
