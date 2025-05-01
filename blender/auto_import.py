import bpy
import os
import tempfile

# Directories
WATCH_DIR = "F:/poc/text_to_3d/TRELLIS/generated_assets"
ASSET_LIBRARY_DIR = "F:/poc/text_to_3d/blender_assets"
COMBINED_BLEND_FILE = os.path.join(ASSET_LIBRARY_DIR, "trellis_assets.blend")

# Create asset library directory if it doesn't exist
os.makedirs(ASSET_LIBRARY_DIR, exist_ok=True)

def register_asset_library():
    """Register the asset library with Blender's preferences"""
    try:
        # Get absolute path for consistency
        absolute_path = os.path.abspath(ASSET_LIBRARY_DIR)
        
        # Check if already registered
        library_exists = False
        asset_libraries = bpy.context.preferences.filepaths.asset_libraries
        for library in asset_libraries:
            if os.path.abspath(library.path) == absolute_path:
                library_exists = True
                print(f"Asset library already registered: {absolute_path}")
                break
        
        # Register if not found
        if not library_exists:
            # Add the library (method depends on Blender version)
            library = None
            if hasattr(asset_libraries, 'new'):
                library = asset_libraries.new(name="TRELLIS Assets")
            else:
                library = asset_libraries.add()
                library.name = "TRELLIS Assets"
            
            library.path = absolute_path
            bpy.ops.wm.save_userpref()
            print(f"Successfully registered asset library: {absolute_path}")
        
        return True
    except Exception as e:
        print(f"Error registering asset library: {e}")
        print(f"Please add manually: Edit > Preferences > File Paths > Asset Libraries")
        return False

def process_all_glb_files():
    """Process all GLB files without disturbing the current scene"""
    # Get all GLB files
    if not os.path.exists(WATCH_DIR):
        print(f"Watch directory does not exist: {WATCH_DIR}")
        return
    
    glb_files = [f for f in os.listdir(WATCH_DIR) if f.endswith('.glb')]
    
    if not glb_files:
        print("No GLB files found in the watch directory.")
        return
    
    print(f"Found {len(glb_files)} GLB file(s). Processing...")
    
    # Print exact file path for debugging
    print(f"Will save to: {COMBINED_BLEND_FILE}")
    
    # Create a temporary Blender script to process files separately
    temp_script = f"""
import bpy
import os

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Process GLB files
files = {glb_files}
watch_dir = r"{WATCH_DIR}"
output_file = r"{COMBINED_BLEND_FILE}"

for glb_file in files:
    filepath = os.path.join(watch_dir, glb_file)
    print(f"Processing: {{glb_file}}")
    
    # Get the file basename for naming
    file_basename = os.path.splitext(glb_file)[0]
    
    # Deselect all objects before import
    bpy.ops.object.select_all(action='DESELECT')
    
    # Import GLB file
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    # Find imported objects
    imported_objects = bpy.context.selected_objects
    if not imported_objects:
        print(f"No objects were imported from {{glb_file}}. Skipping.")
        continue
    
    # Create a temporary collection for organization
    collection = bpy.data.collections.new(f"temp_{{file_basename}}")
    bpy.context.scene.collection.children.link(collection)
    
    # Filter to keep only mesh objects
    mesh_objects = [obj for obj in imported_objects if obj.type == 'MESH']
    
    # Delete non-mesh objects (empties, etc.)
    non_mesh_objects = [obj for obj in imported_objects if obj.type != 'MESH']
    if non_mesh_objects:
        print(f"Removing {{len(non_mesh_objects)}} non-mesh objects")
        for obj in non_mesh_objects:
            bpy.data.objects.remove(obj)
    
    # If no mesh objects found, skip this file
    if not mesh_objects:
        print(f"No mesh objects found in {{glb_file}}. Skipping.")
        bpy.data.collections.remove(collection)
        continue
    
    # Move all mesh objects to the temporary collection
    for obj in mesh_objects:
        for coll in list(obj.users_collection):
            coll.objects.unlink(obj)
        collection.objects.link(obj)
    
    # Select all mesh objects in the collection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(obj.type == 'MESH')
    
    # Set the active object (needed for join operation)
    bpy.context.view_layer.objects.active = next((obj for obj in collection.objects if obj.type == 'MESH'), None)
    
    # Join them into a single object if there are multiple
    if len([obj for obj in collection.objects if obj.type == 'MESH']) > 1:
        bpy.ops.object.join()
    
    # After join, only one object remains (active object)
    merged_obj = bpy.context.active_object
    
    # Rename object and its mesh data with proper name
    merged_obj.name = file_basename
    if merged_obj.data:
        merged_obj.data.name = f"{{file_basename}}_mesh"
    
    # Move merged object out of the temporary collection
    for coll in list(merged_obj.users_collection):
        coll.objects.unlink(merged_obj)
    bpy.context.scene.collection.objects.link(merged_obj)
    
    # Set origin to geometry
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    # Mark merged object as asset
    merged_obj.asset_mark()
    if hasattr(merged_obj, 'asset_data'):
        merged_obj.asset_data.description = f"3D model generated by TRELLIS from {{glb_file}}"
        merged_obj.asset_data.tags.new("TRELLIS")
    
    # Delete the now-empty collection
    bpy.data.collections.remove(collection)
    
    print(f"Created asset object: {{file_basename}}")

# Save the combined file
print(f"Saving all assets to: {{output_file}}")
bpy.ops.wm.save_as_mainfile(filepath=output_file)
print("All assets saved successfully")
"""
    
    # Write temporary script
    temp_script_path = os.path.join(tempfile.gettempdir(), "process_assets.py")
    
    # Also save a copy to the assets directory for inspection
    debug_script_path = os.path.join(ASSET_LIBRARY_DIR, "debug_script.py")
    
    with open(temp_script_path, 'w') as f:
        f.write(temp_script)
    
    # Save a copy for debugging
    with open(debug_script_path, 'w') as f:
        f.write(temp_script)
        
    print(f"Saved debug script to: {debug_script_path}")
    
    # Execute in background Blender process
    try:
        blender_exe = bpy.app.binary_path
        print(f"Using Blender executable: {blender_exe}")
        cmd = [blender_exe, '--background', '--python', temp_script_path]
        
        print(f"Processing assets in background...")
        import subprocess
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Return code: {process.returncode}")
        print(f"Output: {process.stdout}")
        if process.stderr:
            print(f"Error output: {process.stderr}")
        
        if process.returncode == 0:
            print(f"Successfully processed all assets")
            os.remove(temp_script_path)  # Clean up
            return True
        else:
            print(f"Error processing files: {process.stderr}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function"""
    # Register the asset library
    register_asset_library()
    
    # Process all GLB files without changing current scene
    process_all_glb_files()
    
    # Final message
    print("All files processed. Assets available in the Asset Browser under 'TRELLIS Assets'")

# Entry point
if __name__ == "__main__":
    main()