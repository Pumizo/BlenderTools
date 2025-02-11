# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2015: SCS Software


class Reflective:
    GEOM_NODE = "Geometry"
    BASE_TEX_NODE = "BaseTex"
    VCOLOR_MULT_NODE = "VertexColorMultiplier"
    VCOLOR_SCALE_NODE = "VertexColorScale"
    OUT_MAT_NODE = "InputMaterial"
    OUTPUT_NODE = "Output"

    @staticmethod
    def get_name():
        """Get name of this shader file with full modules path."""
        return __name__

    @staticmethod
    def init(node_tree):
        """Initialize node tree with links for this shader.

        :param node_tree: node tree on which this shader should be created
        :type node_tree: bpy.types.NodeTree
        """

        start_pos_x = 0
        start_pos_y = 0

        pos_x_shift = 185

        node_tree.nodes.clear()

        # node creation
        geometry_n = node_tree.nodes.new("ShaderNodeGeometry")
        geometry_n.name = Reflective.GEOM_NODE
        geometry_n.label = Reflective.GEOM_NODE
        geometry_n.location = (start_pos_x - pos_x_shift, start_pos_y + 1900)

        vcol_scale_n = node_tree.nodes.new("ShaderNodeMixRGB")
        vcol_scale_n.name = Reflective.VCOLOR_SCALE_NODE
        vcol_scale_n.label = Reflective.VCOLOR_SCALE_NODE
        vcol_scale_n.location = (start_pos_x + pos_x_shift * 3, start_pos_y + 1750)
        vcol_scale_n.blend_type = "MULTIPLY"
        vcol_scale_n.inputs['Fac'].default_value = 1
        vcol_scale_n.inputs['Color2'].default_value = (4,) * 4

        base_tex_n = node_tree.nodes.new("ShaderNodeTexture")
        base_tex_n.name = Reflective.BASE_TEX_NODE
        base_tex_n.label = Reflective.BASE_TEX_NODE
        base_tex_n.location = (start_pos_x + pos_x_shift, start_pos_y + 1500)

        vcol_mult_n = node_tree.nodes.new("ShaderNodeMixRGB")
        vcol_mult_n.name = Reflective.VCOLOR_MULT_NODE
        vcol_mult_n.label = Reflective.VCOLOR_MULT_NODE
        vcol_mult_n.location = (start_pos_x + pos_x_shift * 4, start_pos_y + 1700)
        vcol_mult_n.blend_type = "MULTIPLY"
        vcol_mult_n.inputs['Fac'].default_value = 1

        out_mat_n = node_tree.nodes.new("ShaderNodeExtendedMaterial")
        out_mat_n.name = Reflective.OUT_MAT_NODE
        out_mat_n.label = Reflective.OUT_MAT_NODE
        if "Refl" in out_mat_n:
            out_mat_n.inputs['Refl'].default_value = 1.0
        elif "Reflectivity" in out_mat_n:
            out_mat_n.inputs['Reflectivity'].default_value = 1.0
        out_mat_n.location = (start_pos_x + pos_x_shift * 7, start_pos_y + 1800)

        output_n = node_tree.nodes.new("ShaderNodeOutput")
        output_n.name = Reflective.OUTPUT_NODE
        output_n.label = Reflective.OUTPUT_NODE
        output_n.location = (start_pos_x + + pos_x_shift * 8, start_pos_y + 1800)

        # links creation
        node_tree.links.new(base_tex_n.inputs['Vector'], geometry_n.outputs['UV'])
        node_tree.links.new(vcol_scale_n.inputs['Color1'], geometry_n.outputs['Vertex Color'])

        node_tree.links.new(vcol_mult_n.inputs['Color1'], vcol_scale_n.outputs['Color'])
        node_tree.links.new(vcol_mult_n.inputs['Color2'], base_tex_n.outputs['Color'])

        node_tree.links.new(out_mat_n.inputs['Color'], vcol_mult_n.outputs['Color'])
        node_tree.links.new(out_mat_n.inputs['Alpha'], base_tex_n.outputs['Value'])

        node_tree.links.new(output_n.inputs['Color'], out_mat_n.outputs['Color'])
        node_tree.links.new(output_n.inputs['Alpha'], out_mat_n.outputs['Alpha'])

    @staticmethod
    def set_material(node_tree, material):
        """Set output material for this shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param material: blender material for used in this tree node as output
        :type material: bpy.types.Material
        """

        node_tree.nodes[Reflective.OUT_MAT_NODE].material = material
        node_tree.nodes[Reflective.OUT_MAT_NODE].use_specular = False
        material.use_transparency = True
        material.transparency_method = "MASK"
        material.emit = 0.02

    @staticmethod
    def set_base_texture(node_tree, texture):
        """Set base texture to shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param texture: texture which should be assignet to base texture node
        :type texture: bpy.types.Texture
        """

        node_tree.nodes[Reflective.BASE_TEX_NODE].texture = texture

    @staticmethod
    def set_base_uv(node_tree, uv_layer):
        """Set UV layer to base texture in shader.

        :param node_tree: node tree of current shader
        :type node_tree: bpy.types.NodeTree
        :param uv_layer: uv layer string used for base texture
        :type uv_layer: str
        """

        node_tree.nodes[Reflective.GEOM_NODE].uv_layer = uv_layer