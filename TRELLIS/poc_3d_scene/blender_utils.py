import os
import winreg
import logging
from glob import glob
import subprocess

def find_blender_in_registry():
    def search_root(name, root):
        found = []
        try:
            with winreg.OpenKey(root, r"SOFTWARE\Classes") as classes_key:
                i = 0
                while True:
                    try:
                        subkey = winreg.EnumKey(classes_key, i)
                        if subkey.lower().startswith("blender"):
                            command_key = fr"{subkey}\shell\open\command"
                            try:
                                with winreg.OpenKey(root, fr"SOFTWARE\Classes\{command_key}") as cmd:
                                    value, _ = winreg.QueryValueEx(cmd, None)
                                    parts = value.split('"')
                                    for part in parts:
                                        if os.path.isfile(part) and part.lower().endswith("blender.exe"):
                                            found.append((f"{name}\\{subkey}", part))
                            except FileNotFoundError:
                                pass
                        i += 1
                    except OSError:
                        break
        except PermissionError:
            logging.warning(f"Permission denied reading {name}\\SOFTWARE\\Classes")
        return found

    results = []
    results += search_root("HKLM", winreg.HKEY_LOCAL_MACHINE)
    results += search_root("HKCU", winreg.HKEY_CURRENT_USER)
    return results

def find_blender_in_app_paths():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\blender.exe") as key:
            value, _ = winreg.QueryValueEx(key, None)
            if os.path.isfile(value):
                return [("AppPaths", value)]
    except FileNotFoundError:
        return []
    return []

def search_common_blender_dirs():
    search_paths = [
        r"C:\Program Files\Blender Foundation",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Blender Foundation"),
        os.path.expandvars(r"%PROGRAMFILES%\Blender Foundation"),
        os.path.expandvars(r"%APPDATA%\Blender Foundation"),
        os.path.expandvars(r"%USERPROFILE%\Downloads"),
    ]

    found = []
    for base in search_paths:
        if os.path.isdir(base):
            matches = glob(os.path.join(base, "**", "blender.exe"), recursive=True)
            for match in matches:
                found.append(("FolderScan", match))
    return found

# Optional: full scan of C:\ drive (very slow)
def full_disk_scan(enable=False):
    found = []
    if not enable:
        return found
    print("🔍 Running full C:\\ drive scan (this may take several minutes)...")
    for root, dirs, files in os.walk("C:\\"):
        for name in files:
            if name.lower() == "blender.exe":
                full_path = os.path.join(root, name)
                found.append(("FullScan", full_path))
    return found

# WindowsApps Alias check (fast)
def find_windowsapps_blender_alias():
    alias = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\blender.exe")
    if os.path.exists(alias):
        return alias
    return None


# PowerShell Query (for Store-installed Blender)
def find_windows_store_blender_path():
    cmd = ['powershell', '-Command',
           "Get-AppxPackage *blender* | Select -ExpandProperty InstallLocation"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None

def find_all_blender_installations(full_scan=False):
    all_found = []
    
    # Check if Blender is found via WindowsApps alias
    alias = find_windowsapps_blender_alias()
    if alias:
        all_found.append(("WindowsAppsAlias", alias))

    # Check if Blender is found via PowerShell query (Store version)
    store_path = find_windows_store_blender_path()
    if store_path:
        all_found.append(("WindowsStore", os.path.join(store_path, "blender.exe")))
    
    # Check registry paths
    all_found += find_blender_in_registry()
    
    # Check App Paths registry
    all_found += find_blender_in_app_paths()
    
    # Check common install directories
    all_found += search_common_blender_dirs()
    
    # Optional: full scan of C:\ drive
    all_found += full_disk_scan(full_scan)
    
    return all_found

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Print environment variable
    print(f"ATTN_BACKEND: {os.environ.get('ATTN_BACKEND', 'Not set')}")
    
    installations = {
        "windowsapps_alias": [],
        "windows_store": [],
        "registry": [],
        "app_paths": [],
        "directory_scan": [],
        "full_disk_scan": []
    }
    
    # Check WindowsApps alias
    alias = find_windowsapps_blender_alias()
    if alias:
        installations["windowsapps_alias"].append(alias)

    # Check Windows Store installation
    store_path = find_windows_store_blender_path()
    if store_path:
        # Append blender.exe to the store path
        store_path = os.path.join(store_path, "blender.exe")
        installations["windows_store"].append(store_path)
    
    # Check registry paths
    registry_results = find_blender_in_registry()
    if registry_results:
        installations["registry"] = [path for _, path in registry_results]
    
    # Check App Paths registry
    app_paths_results = find_blender_in_app_paths()
    if app_paths_results:
        installations["app_paths"] = [path for _, path in app_paths_results]
    
    # Check common install directories
    dir_results = search_common_blender_dirs()
    if dir_results:
        installations["directory_scan"] = [path for _, path in dir_results]
    
    # Optional: full scan of C:\ drive
    full_scan_results = full_disk_scan(enable=False)
    if full_scan_results:
        installations["full_disk_scan"] = [path for _, path in full_scan_results]

    # Remove empty lists
    installations = {k: v for k, v in installations.items() if v}
    
    # Print results
    if installations:
        print("✅ Blender installations found:")
        for method, paths in installations.items():
            print(f"\nFound via {method.replace('_', ' ').title()}:")
            for path in paths:
                # Use repr() to show the exact string including escape characters
                print(f"  {repr(path)}")
    else:
        print("❌ No Blender installations found via any method.")
    
    # Return the dictionary
    print("\nInstallations dictionary:")
    print(installations)
