import subprocess

def take_screenshot(angle: float):
    result = subprocess.run(
        ["node", "../renderer/screenshot.js", str(angle)],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("Error:", result.stderr)
    else:
        print(result.stdout)

# Example usage
take_screenshot(1.57)

