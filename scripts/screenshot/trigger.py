import subprocess

def trigger_screenshots():
    result = subprocess.run(
        ["node", "../../../truck-load-view/take_screenshot.js"],
        capture_output=True,
        text=True
    )
    print(result.stdout)

trigger_screenshots()
