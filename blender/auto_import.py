import bpy
import os
import time
from pathlib import Path
import math

# Set this to your output_glb directory
WATCH_DIR = "F:/poc/text_to_3d/TRELLIS/generated_assets"

class GLBWatcherOperator(bpy.types.Operator):
    """Watch directory for new GLB files"""
    bl_idname = "wm.glb_watcher"
    bl_label = "GLB Watcher"
    
    _timer = None
    existing_files = set()
    processing_files = set()  # Track files being processed
    is_running = False  # Flag to control the watcher
    grid_size = 2.0  # Distance between objects in the grid
    current_x = 0.0  # Current X position for new objects
    current_z = 0.0  # Current Z position for new objects
    max_objects_per_row = 5 # Maximum number of objects per row
    
    def get_next_position(self):
        """Calculate the next position for a new object in a grid layout"""
        # Calculate row and column
        total_objects = len(bpy.data.objects)
        row = total_objects // self.max_objects_per_row
        col = total_objects % self.max_objects_per_row
        
        # Calculate position
        x = col * self.grid_size
        z = -row * self.grid_size  # Negative Z to move forward
        
        return x, 0.0, z
    
    def modal(self, context, event):
        if not self.is_running:
            self.cancel(context)
            return {'FINISHED'}
            
        if event.type == 'TIMER':
            try:
                # Check for new files
                current_files = set(f for f in os.listdir(WATCH_DIR) if f.endswith('.glb'))
                new_files = current_files - self.existing_files - self.processing_files
                
                if new_files:
                    # Import the newest file
                    newest_file = max(new_files, key=lambda f: os.path.getctime(os.path.join(WATCH_DIR, f)))
                    filepath = os.path.join(WATCH_DIR, newest_file)
                    
                    # Check if file is still being written
                    initial_size = os.path.getsize(filepath)
                    time.sleep(0.5)  # Wait a bit
                    if os.path.getsize(filepath) != initial_size:
                        print(f"File {newest_file} is still being written, skipping...")
                        return {'PASS_THROUGH'}
                    
                    # Add to processing set
                    self.processing_files.add(newest_file)
                    
                    try:
                        # Get the next position for the new object
                        next_pos = self.get_next_position()
                        
                        # Import the new GLB file
                        bpy.ops.import_scene.gltf(filepath=filepath)
                        
                        # Move the newly imported object to the next position
                        for obj in bpy.context.selected_objects:
                            obj.location = next_pos
                        
                        # Try to center view, but don't fail if it doesn't work
                        try:
                            for area in bpy.context.screen.areas:
                                if area.type == 'VIEW_3D':
                                    for region in area.regions:
                                        if region.type == 'WINDOW':
                                            override = {'area': area, 'region': region}
                                            bpy.ops.view3d.view_all(override)
                                            break
                        except Exception as e:
                            print(f"Could not center view: {str(e)}")
                        
                        print(f"Successfully imported: {newest_file}")
                        
                        # Update existing files list
                        self.existing_files = current_files
                        
                    except Exception as e:
                        print(f"Error importing {newest_file}: {str(e)}")
                    
                    finally:
                        # Remove from processing set
                        self.processing_files.discard(newest_file)
            
            except Exception as e:
                print(f"Error in watcher: {str(e)}")
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        # Initialize the existing files list
        self.existing_files = set(f for f in os.listdir(WATCH_DIR) if f.endswith('.glb'))
        self.processing_files = set()
        self.is_running = True
        
        # Start the timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        self.is_running = False
        print("GLB Watcher stopped")

class GLBWatcherStopOperator(bpy.types.Operator):
    """Stop the GLB file watcher"""
    bl_idname = "wm.glb_watcher_stop"
    bl_label = "Stop GLB Watcher"
    
    def execute(self, context):
        # Find and stop any running watchers
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'window': window, 'screen': window.screen, 'area': area, 'region': region}
                        bpy.ops.wm.glb_watcher(override)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(GLBWatcherOperator)
    bpy.utils.register_class(GLBWatcherStopOperator)

def unregister():
    bpy.utils.unregister_class(GLBWatcherOperator)
    bpy.utils.unregister_class(GLBWatcherStopOperator)

if __name__ == "__main__":
    register()
    
    # Start the watcher
    bpy.ops.wm.glb_watcher()