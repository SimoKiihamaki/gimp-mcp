"""
Analysis Results Dialog for GIMP.

This module provides a dialog for displaying image analysis results.
"""
from gimpfu import *

def show_analysis_results(image, analysis):
    """
    Show a dialog displaying image analysis results.
    
    Args:
        image: The GIMP image object
        analysis: Image analysis results from the server
        
    Returns:
        None
    """
    # Create the dialog
    dialog = gimp.Dialog("Image Analysis Results", "analysis-results-dialog",
                       None, 0, None, None)
    dialog.set_size_request(500, 400)
    
    # Create a vertical box for the dialog content
    vbox = dialog.vbox
    
    # Add a title
    title_label = gtk.Label()
    title_label.set_markup("<b>Image Analysis Results</b>")
    vbox.pack_start(title_label, False, False, 10)
    title_label.show()
    
    # Create a scrolled window for the results
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    vbox.pack_start(scrolled_window, True, True, 0)
    scrolled_window.show()
    
    # Create a vertical box for the analysis results
    results_vbox = gtk.VBox(False, 5)
    scrolled_window.add_with_viewport(results_vbox)
    results_vbox.show()
    
    # Add image dimensions
    if "dimensions" in analysis:
        dimensions = analysis["dimensions"]
        dim_frame = create_section_frame("Dimensions")
        dim_vbox = gtk.VBox(False, 5)
        dim_frame.add(dim_vbox)
        
        width = dimensions.get("width", 0)
        height = dimensions.get("height", 0)
        aspect_ratio = dimensions.get("aspect_ratio", 0)
        
        dim_vbox.pack_start(gtk.Label(f"Width: {width} pixels"), False, False, 0)
        dim_vbox.pack_start(gtk.Label(f"Height: {height} pixels"), False, False, 0)
        dim_vbox.pack_start(gtk.Label(f"Aspect Ratio: {aspect_ratio}"), False, False, 0)
        
        results_vbox.pack_start(dim_frame, False, False, 5)
        dim_vbox.show_all()
        dim_frame.show()
    
    # Add color information
    if "color_analysis" in analysis:
        color_analysis = analysis["color_analysis"]
        color_frame = create_section_frame("Color Analysis")
        color_vbox = gtk.VBox(False, 5)
        color_frame.add(color_vbox)
        
        # Add average color
        if "average_color" in color_analysis:
            avg_color = color_analysis["average_color"]
            rgb = avg_color.get("rgb", (0, 0, 0))
            hex_color = avg_color.get("hex", "#000000")
            
            avg_color_label = gtk.Label(f"Average Color: RGB({rgb[0]}, {rgb[1]}, {rgb[2]}) - {hex_color}")
            color_vbox.pack_start(avg_color_label, False, False, 0)
            
            # Add a color swatch
            color_swatch = gtk.Frame()
            color_swatch.set_size_request(50, 20)
            color_swatch.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(hex_color))
            color_vbox.pack_start(color_swatch, False, False, 5)
        
        # Add brightness and contrast
        brightness = color_analysis.get("brightness", 0)
        contrast = color_analysis.get("contrast", 0)
        is_grayscale = color_analysis.get("is_grayscale", False)
        
        color_vbox.pack_start(gtk.Label(f"Brightness: {brightness:.1f}"), False, False, 0)
        color_vbox.pack_start(gtk.Label(f"Contrast: {contrast:.1f}"), False, False, 0)
        color_vbox.pack_start(gtk.Label(f"Grayscale: {'Yes' if is_grayscale else 'No'}"), False, False, 0)
        
        # Add dominant colors
        if "dominant_colors" in color_analysis:
            dominant_colors = color_analysis["dominant_colors"]
            dom_color_label = gtk.Label(f"Dominant Colors: {', '.join(dominant_colors)}")
            color_vbox.pack_start(dom_color_label, False, False, 0)
        
        results_vbox.pack_start(color_frame, False, False, 5)
        color_vbox.show_all()
        color_frame.show()
    
    # Add layer information
    if "layer_count" in analysis:
        layer_count = analysis["layer_count"]
        visible_layer_count = analysis.get("visible_layer_count", 0)
        
        layer_frame = create_section_frame("Layers")
        layer_vbox = gtk.VBox(False, 5)
        layer_frame.add(layer_vbox)
        
        layer_vbox.pack_start(gtk.Label(f"Total Layers: {layer_count}"), False, False, 0)
        layer_vbox.pack_start(gtk.Label(f"Visible Layers: {visible_layer_count}"), False, False, 0)
        
        # Add detailed layer analysis if available
        if "layer_analysis" in analysis:
            layer_analysis = analysis["layer_analysis"]
            layer_tree = gtk.TreeView()
            layer_store = gtk.ListStore(str, str, int, str, bool)
            
            layer_tree.set_model(layer_store)
            
            # Add columns
            layer_tree.append_column(gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=0))
            layer_tree.append_column(gtk.TreeViewColumn("Blend Mode", gtk.CellRendererText(), text=1))
            layer_tree.append_column(gtk.TreeViewColumn("Opacity", gtk.CellRendererText(), text=2))
            
            visible_renderer = gtk.CellRendererToggle()
            visible_renderer.set_property("activatable", False)
            visible_column = gtk.TreeViewColumn("Visible", visible_renderer)
            visible_column.add_attribute(visible_renderer, "active", 4)
            layer_tree.append_column(visible_column)
            
            # Add layer data
            for layer in layer_analysis:
                layer_store.append([
                    layer.get("name", "Unnamed"),
                    layer.get("blend_mode", "Normal"),
                    layer.get("opacity", 100),
                    "Group" if layer.get("is_group", False) else "Layer",
                    layer.get("visible", False)
                ])
            
            # Add tree to a scrolled window
            layer_scroll = gtk.ScrolledWindow()
            layer_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            layer_scroll.set_size_request(-1, 100)
            layer_scroll.add(layer_tree)
            layer_vbox.pack_start(layer_scroll, True, True, 5)
        
        results_vbox.pack_start(layer_frame, False, False, 5)
        layer_vbox.show_all()
        layer_frame.show()
    
    # Add selection information
    if "has_selection" in analysis:
        has_selection = analysis["has_selection"]
        
        selection_frame = create_section_frame("Selection")
        selection_vbox = gtk.VBox(False, 5)
        selection_frame.add(selection_vbox)
        
        if has_selection and "selection_size" in analysis:
            selection_size = analysis["selection_size"]
            width = selection_size.get("width", 0)
            height = selection_size.get("height", 0)
            area = selection_size.get("area", 0)
            
            selection_vbox.pack_start(gtk.Label(f"Selection Present: Yes"), False, False, 0)
            selection_vbox.pack_start(gtk.Label(f"Selection Size: {width}x{height} pixels"), False, False, 0)
            selection_vbox.pack_start(gtk.Label(f"Selection Area: {area} pixels²"), False, False, 0)
        else:
            selection_vbox.pack_start(gtk.Label("Selection Present: No"), False, False, 0)
        
        results_vbox.pack_start(selection_frame, False, False, 5)
        selection_vbox.show_all()
        selection_frame.show()
    
    # Add detected objects (if any)
    if "detected_objects" in analysis:
        objects = analysis["detected_objects"]
        
        if objects and objects[0]["label"] != "unknown":
            objects_frame = create_section_frame("Detected Objects")
            objects_vbox = gtk.VBox(False, 5)
            objects_frame.add(objects_vbox)
            
            # Create a list of objects
            for obj in objects:
                label = obj.get("label", "unknown")
                confidence = obj.get("confidence", 0.0)
                
                obj_label = gtk.Label(f"{label} (Confidence: {confidence:.2f})")
                obj_label.set_alignment(0.0, 0.5)  # Left-align
                objects_vbox.pack_start(obj_label, False, False, 0)
            
            results_vbox.pack_start(objects_frame, False, False, 5)
            objects_vbox.show_all()
            objects_frame.show()
    
    # Add a scene type if available
    if "scene_type" in analysis and analysis["scene_type"] != "unknown":
        scene_frame = create_section_frame("Scene Analysis")
        scene_vbox = gtk.VBox(False, 5)
        scene_frame.add(scene_vbox)
        
        scene_type = analysis["scene_type"]
        style = analysis.get("style", "unknown")
        
        scene_vbox.pack_start(gtk.Label(f"Scene Type: {scene_type}"), False, False, 0)
        
        if style != "unknown":
            scene_vbox.pack_start(gtk.Label(f"Style: {style}"), False, False, 0)
        
        results_vbox.pack_start(scene_frame, False, False, 5)
        scene_vbox.show_all()
        scene_frame.show()
    
    # Add OK button at the bottom
    dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    
    # Show the dialog
    dialog.show()
    
    # Run the dialog
    dialog.run()
    dialog.destroy()

def create_section_frame(title):
    """
    Create a framed section for the analysis results.
    
    Args:
        title: The title for the section
        
    Returns:
        gtk.Frame: The created frame
    """
    frame = gtk.Frame(f"<b>{title}</b>")
    frame.get_label_widget().set_use_markup(True)
    frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
    frame.set_border_width(5)
    
    return frame
