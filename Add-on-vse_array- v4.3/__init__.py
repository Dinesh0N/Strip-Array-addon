bl_info = {
    "name": "VSE Strip Array Duplicate",
    "description": "Create an array of duplicated strips with customizable options and Displays the number of strips.",
    "author": "Dinesh",
    "version": (1, 0, 2),
    "blender": (2, 8, 0),
    "category": "Sequencer",
    "location": "Sequencer > ToolTab",
}

import bpy
import random
import os

# Enum for Offset Type
class OffsetTypeEnum(bpy.types.PropertyGroup):
    FRAME_BASED: bpy.props.EnumProperty(
        name="Offset Type",
        description="Choose the type of offset",
        items=[
            ('FRAME_BASED', "Frame", "Offset strips in frames"),
            ('TIME_BASED', "Time", "Offset strips in seconds")
        ],
        default='FRAME_BASED'
    )

class VSE_OT_ArrayDuplicate(bpy.types.Operator):
    """Duplicate strips in the VSE with customizable array parameters"""
    bl_idname = "sequencer.array_duplicate"
    bl_label = "Array Duplicate Strips"
    bl_options = {'REGISTER', 'UNDO'}

    # Properties for the duplication options
    strip_count: bpy.props.IntProperty(
        name="Strip Count",
        description="Number of duplicate strips",
        default=5,
        min=1
    )
    strip_offset: bpy.props.FloatProperty(
        name="Strip Offset",
        description="Offset between strips (in frames or time)",
        default=1.0,
        min=0.0
    )
    channel_offset: bpy.props.IntProperty(
        name="Channel Offset",
        description="Channel offset for each duplicated strip",
        default=0,
        min=-10,
        max=10
    )
    random_offset: bpy.props.FloatProperty(
        name="Random Offset",
        description="Random offset for each strip (in frames)",
        default=0.0,
        min=0.0
    )
    random_color: bpy.props.BoolProperty(
        name="Random Color Tag",
        description="Assign random colors to each strip",
        default=False
    )
    offset_type: bpy.props.EnumProperty(
        name="Offset Type",
        description="Select offset type for duplication",
        items=[
            ('FRAME_BASED', "Frame", "Offset strips in frames"),
            ('TIME_BASED', "Time", "Offset strips in seconds")
        ],
        default='TIME_BASED'
    )
    toggle_connect: bpy.props.BoolProperty(
        name="Toggle Connect",
        description="Toggle connecting/disconnecting the duplicated strips",
        default=True
    )

    def assign_random_color(self, strip):
        """Assigns a random color tag to the strip"""
        colors = ["COLOR_01", "COLOR_02", "COLOR_03", "COLOR_04", "COLOR_05", "COLOR_06", "COLOR_07", "COLOR_08", "COLOR_09"]
        strip.color_tag = random.choice(colors)

    def duplicate_strip(self, sequencer, strip, frame_start_offset, new_channel):
        """Duplicate a strip based on its type"""
        new_strip = None

        if isinstance(strip, bpy.types.ImageSequence):
            filepath = os.path.join(strip.directory, strip.elements[0].filename)
            new_strip = sequencer.sequences.new_image(
                name=f"{strip.name}_copy",
                filepath=filepath,
                frame_start=frame_start_offset,
                channel=new_channel
            )
            new_strip.frame_final_duration = strip.frame_final_duration

        elif isinstance(strip, bpy.types.MovieSequence):
            new_strip = sequencer.sequences.new_movie(
                name=f"{strip.name}_copy",
                filepath=strip.filepath,
                frame_start=frame_start_offset,
                channel=new_channel
            )
            new_strip.frame_final_duration = strip.frame_final_duration

        elif isinstance(strip, bpy.types.SoundSequence):
            new_strip = sequencer.sequences.new_sound(
                name=f"{strip.name}_copy",
                filepath=strip.sound.filepath,
                frame_start=frame_start_offset,
                channel=new_channel
            )
            new_strip.frame_final_duration = strip.frame_final_duration

        elif isinstance(strip, bpy.types.SceneSequence):
            new_strip = sequencer.sequences.new_scene(
                name=f"{strip.name}_copy",
                scene=strip.scene,
                frame_start=frame_start_offset,
                channel=new_channel
            )
            new_strip.frame_final_duration = strip.frame_final_duration

        elif isinstance(strip, bpy.types.ColorSequence):
            new_strip = sequencer.sequences.new_effect(
                name=f"{strip.name}_copy",
                type='COLOR',
                frame_start=frame_start_offset,
                frame_end=frame_start_offset + strip.frame_final_duration,
                channel=new_channel
            )
            new_strip.color = strip.color

        elif isinstance(strip, bpy.types.TextSequence):
            new_strip = sequencer.sequences.new_effect(
                name=f"{strip.name}_copy",
                type='TEXT',
                frame_start=frame_start_offset,
                frame_end=frame_start_offset + strip.frame_final_duration,
                channel=new_channel
            )
            new_strip.text = strip.text

        elif isinstance(strip, bpy.types.AdjustmentSequence):
            new_strip = sequencer.sequences.new_effect(
                name=f"{strip.name}_copy",
                type='ADJUSTMENT',
                frame_start=frame_start_offset,
                frame_end=frame_start_offset + strip.frame_final_duration,
                channel=new_channel
            )

        elif isinstance(strip, bpy.types.MaskSequence):
            new_strip = sequencer.sequences.new_mask(
                name=f"{strip.name}_copy",
                mask=strip.mask,
                frame_start=frame_start_offset,
                channel=new_channel
            )
            new_strip.frame_final_duration = strip.frame_final_duration

        return new_strip

    def execute(self, context):
        sequencer = context.scene.sequence_editor
        selected_strips = [s for s in sequencer.sequences if s.select]

        if not selected_strips:
            self.report({'WARNING'}, "No strips selected!")
            return {'CANCELLED'}

        for strip in selected_strips:
            start_frame = strip.frame_start
            channel = strip.channel

            for i in range(1, self.strip_count):
                if self.offset_type == 'FRAME_BASED':
                    frame_start_offset = int(start_frame + (i * self.strip_offset) + random.uniform(0, self.random_offset))
                else:  # TIME_BASED
                    time_offset = self.strip_offset * bpy.context.scene.render.fps  # Convert to frames
                    frame_start_offset = int(start_frame + (i * time_offset) + random.uniform(0, self.random_offset))

                new_channel = channel + (i * self.channel_offset)

                # Ensure that the channel is not negative
                if new_channel < 1:
                    new_channel = 1

                # Adjust for potential overlap
                frame_end_offset = frame_start_offset + strip.frame_final_duration
                existing_strips = [s for s in sequencer.sequences if s.channel == new_channel and
                                   s.frame_start < frame_end_offset and frame_start_offset < s.frame_start + s.frame_final_duration]

                # Shift frame_start_offset until no overlap
                while existing_strips:
                    frame_start_offset += 1  # Increment the start frame
                    frame_end_offset = frame_start_offset + strip.frame_final_duration
                    existing_strips = [s for s in sequencer.sequences if s.channel == new_channel and
                                       s.frame_start < frame_end_offset and frame_start_offset < s.frame_start + s.frame_final_duration]

                # Duplicate the strip based on its type
                new_strip = self.duplicate_strip(sequencer, strip, frame_start_offset, new_channel)
                if not new_strip:
                    self.report({'WARNING'}, f"Cannot duplicate strip type: {type(strip).__name__}")
                    continue

                if self.random_color:
                    self.assign_random_color(new_strip)

        # Handle the connect/disconnect functionality
        if self.toggle_connect:
            bpy.ops.sequencer.connect(toggle=True)
        else:
            bpy.ops.sequencer.disconnect()

        return {'FINISHED'}

class VSE_OT_OffsetSelectedStrips(bpy.types.Operator):
    """Offset selected strips with customizable"""
    bl_idname = "sequencer.offset_selected_strips"
    bl_label = "Offset Selected Strips"
    bl_options = {'REGISTER', 'UNDO'}

    strip_offset: bpy.props.FloatProperty(
        name="Strip Offset",
        description="Offset between strips in frames (incremental)",
        default=10.0,
        min=0.0
    )

    channel_offset: bpy.props.IntProperty(
        name="Channel Offset",
        description="Channel offset between strips (incremental)",
        default=0,
        min=-10,
        max=10
    )

    offset_type: bpy.props.EnumProperty(
        name="Offset Type",
        description="Select offset type for offsetting",
        items=[
            ('FRAME_BASED', "Frame", "Offset strips in frames"),
            ('TIME_BASED', "Time", "Offset strips in seconds")
        ],
        default='FRAME_BASED'
    )

    def execute(self, context):
        sequencer = context.scene.sequence_editor
        selected_strips = [s for s in sequencer.sequences if s.select]

        if not selected_strips:
            self.report({'WARNING'}, "No strips selected!")
            return {'CANCELLED'}

        selected_strips.sort(key=lambda strip: strip.frame_start)

        base_frame_start = selected_strips[0].frame_start
        base_channel = selected_strips[0].channel

        # First, handle frame offset (without changing channels)
        for i, strip in enumerate(selected_strips):
            # Increment the frame start for each strip (ensure strips do not overlap)
            if i > 0:
                if self.offset_type == 'FRAME_BASED':
                    strip.frame_start = base_frame_start + (i * self.strip_offset)
                else:  # TIME_BASED
                    time_offset = self.strip_offset * bpy.context.scene.render.fps  # Convert to frames
                    strip.frame_start = base_frame_start + (i * time_offset)

        # Now, handle channel assignment to avoid auto-pushing
        for i, strip in enumerate(selected_strips):
            # Assign incremental channel offsets after frame offset is done
            strip.channel = base_channel + (i * self.channel_offset)

            # Ensure channel is valid and not negative
            if strip.channel < 1:
                strip.channel = 1

        return {'FINISHED'}


class VSE_OT_ApplyRandomColor(bpy.types.Operator):
    """Apply random colors to selected strips"""
    bl_idname = "sequencer.apply_random_color"
    bl_label = "Apply Random Color"
    bl_options = {'REGISTER', 'UNDO'}

    def assign_random_color(self, strip):
        """Assigns a random color tag to the strip"""
        colors = ["COLOR_01", "COLOR_02", "COLOR_03", "COLOR_04", "COLOR_05", "COLOR_06", "COLOR_07", "COLOR_08", "COLOR_09"]
        strip.color_tag = random.choice(colors)

    def execute(self, context):
        sequencer = context.scene.sequence_editor
        selected_strips = [s for s in sequencer.sequences if s.select]

        if not selected_strips:
            self.report({'WARNING'}, "No strips selected!")
            return {'CANCELLED'}

        for strip in selected_strips:
            self.assign_random_color(strip)

        return {'FINISHED'}

# Displays the number of total and selected strips
def draw_strip_count(self, context):
    scene = context.scene
    vse = scene.sequence_editor

    if vse and vse.sequences:
        total_strips = len(vse.sequences)
        selected_strips = len([strip for strip in vse.sequences if strip.select])
    else:
        total_strips = 0
        selected_strips = 0

    layout = self.layout
    layout.label(text=f"Strips: {selected_strips}/{total_strips}")

def update_strip_count(self, context):
    # Refresh the header whenever the selection changes
    for area in context.screen.areas:
        if area.type == 'SEQUENCE_EDITOR':
            area.tag_redraw()        

class VSE_PT_ArrayDuplicatePanel(bpy.types.Panel):
    """UI panel to expose the Array Duplicate operator"""
    bl_label = "Array Duplicate"
    bl_idname = "SEQUENCER_PT_array_duplicate"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        operator = layout.operator("sequencer.array_duplicate", icon='MOD_ARRAY')


class VSE_PT_OffsetSelectedStripsPanel(bpy.types.Panel):
    """UI Panel for offsetting selected strips in the VSE"""
    bl_label = "Strips Offset"
    bl_idname = "SEQUENCER_PT_offset_selected_strips"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        operator = layout.operator("sequencer.offset_selected_strips", icon='CENTER_ONLY')

        # Add button to apply random colors to selected strips
        layout.operator("sequencer.apply_random_color", text="Apply Random Color", icon='COLOR')

# Registration
classes = [
    OffsetTypeEnum,
    VSE_OT_ArrayDuplicate,
    VSE_OT_OffsetSelectedStrips,
    VSE_OT_ApplyRandomColor,
    VSE_PT_ArrayDuplicatePanel,
    VSE_PT_OffsetSelectedStripsPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.SEQUENCER_HT_header.append(draw_strip_count)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.SEQUENCER_HT_header.remove(draw_strip_count) 

if __name__ == "__main__":
    register()