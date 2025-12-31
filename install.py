import os, sys, subprocess, platform, site

def install():
    print("📦 Installing gtasks-cli...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "gtasks-cli"])

    # Determine Script paths
    user_base = site.getuserbase()
    path_to_add = ""

    if platform.system() == "Windows":
        # Usually: C:\Users\Name\AppData\Roaming\Python\Python313\Scripts
        path_to_add = os.path.join(user_base, f"Python{sys.version_info.major}{sys.version_info.minor}", "Scripts")
        if not os.path.exists(path_to_add): # Fallback
            path_to_add = os.path.join(user_base, "Scripts")
        
        print(f"🔗 Adding to Windows PATH: {path_to_add}")
        os.system(f'setx PATH "%PATH%;{path_to_add}"')
        print("✅ SUCCESS: Please RESTART your terminal to use the 'gtasks' command.")

    else:
        # macOS / Linux
        path_to_add = os.path.join(user_base, "bin")
        shell_file = os.path.expanduser("~/.zshrc" if "zsh" in os.environ.get("SHELL", "") else "~/.bashrc")
        
        with open(shell_file, "a") as f:
            f.write(f'\nexport PATH="$PATH:{path_to_add}"\n')
        
        print(f"✅ SUCCESS: Added to {shell_file}. Run 'source {shell_file}' to update current session.")

if __name__ == "__main__":
    install()
