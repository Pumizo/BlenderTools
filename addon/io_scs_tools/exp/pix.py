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

# Copyright (C) 2013-2014: SCS Software

import bpy
import os
from collections import OrderedDict
from io_scs_tools.utils import path as _path_utils
from io_scs_tools.utils import get_scs_globals as _get_scs_globals
from io_scs_tools.utils.printout import lprint
from io_scs_tools.exp import pia as _pia
from io_scs_tools.exp import pic as _pic
from io_scs_tools.exp import pip as _pip
from io_scs_tools.exp import pis as _pis
from io_scs_tools.exp import pit as _pit
from io_scs_tools.exp.pim import exporter as _pim_exporter


def _get_objects_by_type(blender_objects):
    """Gets lists for different types of objects used by SCS.
    It actually returns: mesh objects, locators (prefab, model, collision) and armature object.

    :param blender_objects: list of the objects that should be sorted by type
    :type blender_objects: list of bpy.types.Object
    :return: more lists of objects in order: meshes, prefab_locators, model_locators, collision_locators and armutare object as last
    :rtype: list of [list]
    """

    prefab_locator_list = []
    model_locator_list = []
    collision_locator_list = []
    mesh_object_list = []
    armature_object = None

    for obj in blender_objects:

        # LOCATORS
        if obj.type == 'EMPTY':
            if obj.scs_props.locator_type == 'Prefab':
                prefab_locator_list.append(obj)
            elif obj.scs_props.locator_type == 'Model':
                model_locator_list.append(obj)
            elif obj.scs_props.locator_type == 'Collision':
                collision_locator_list.append(obj)

        # ARMATURES
        elif obj.type == 'ARMATURE':
            if not armature_object:
                armature_object = obj
            else:
                lprint("W More armatures detected on SCS Root object, only first one will be used!")

        # MESHES
        elif obj.type == 'MESH':

            # MESH OBJECTS
            if obj.data.scs_props.locator_preview_model_path == "":  # Export object only if it's not a Preview Model...
                mesh_object_list.append(obj)

        else:
            print('!!! - Unhandled object type: %r' % str(obj.type))

    return mesh_object_list, prefab_locator_list, model_locator_list, collision_locator_list, armature_object


def _get_initial_selection(content_type):
    """
    Takes content type and returns initial object list.
    :param content_type:
    :return:
    """
    if content_type == 'selection':
        init_obj_list = bpy.context.selected_objects
    elif content_type == 'scene':
        init_obj_list = bpy.context.scene.objects
    elif content_type == 'scenes':
        init_obj_list = bpy.data.objects
    else:
        init_obj_list = bpy.context.selected_objects
        lprint('W Unkown "Selection type" - %r. Using "Selection Only".', content_type)
    return init_obj_list


def export(dirpath, root_object, game_object_list):
    """The main export function.

    :param dirpath: The main Filepath where most of the Files will be exported
    :type dirpath: str
    :param root_object: This is the "SCS Root Object" and parent object of all objects in "game_object_list" and carries many settings for the
    whole "SCS Game Object"
    :type root_object: bpy.types.Object
    :param game_object_list: This is a simple list of all objects belonging to the "SCS Game Object", which can be further reduced of invalid objects
    :type game_object_list: list
    :return: Return state statuses (Usually 'FINISHED')
    :rtype: dict
    """
    import time

    t = time.time()
    context = bpy.context
    context.window.cursor_modal_set('WAIT')

    # GROUP OBJECTS BY TYPE
    (
        mesh_objects,
        prefab_locators,
        model_locators,
        collision_locators,
        armature_object
    ) = _get_objects_by_type(game_object_list)

    skeleton_filepath = root_object.name + ".pis"  # NOTE: if no skeleton is exported name of it should be there anyway
    if armature_object and root_object.scs_props.scs_root_animated:

        skeleton_filepath = _path_utils.get_skeleton_relative_filepath(armature_object, dirpath, root_object.name)

        if len(mesh_objects) == 0:
            context.window.cursor_modal_restore()
            lprint("E Animated SCS Game Object has to have at least one mesh object! SCS Game Object %r won't be exported!", (root_object.name,))
            return False

    # EXPORT
    scs_globals = _get_scs_globals()
    export_success = True
    used_parts = OrderedDict()  # dictionary of parts which are actually used in this game object
    used_materials = []
    used_bones = OrderedDict()  # dictionary of bones which are actually used in this game object

    # EXPORT PIM
    if scs_globals.export_pim_file:
        in_args = (dirpath, root_object, armature_object, skeleton_filepath, mesh_objects, model_locators)
        out_args = (used_parts, used_materials, used_bones)
        export_success = _pim_exporter.execute(*(in_args + out_args))

        # EXPORT PIC
        if scs_globals.export_pic_file and export_success:
            if collision_locators:
                in_args = (collision_locators, dirpath + os.sep + root_object.name, root_object.name)
                out_args = (used_parts,)
                export_success = _pic.export(*(in_args + out_args))
            else:
                lprint("I No collider locator objects to export.")

    # EXPORT PIT
    if scs_globals.export_pit_file and export_success:
        in_args = (root_object, used_parts, used_materials, context.scene, dirpath + os.sep + root_object.name)
        export_success = _pit.export(*in_args)

    # EXPORT PIP
    if scs_globals.export_pip_file and prefab_locators and export_success:
        in_args = (prefab_locators, dirpath + os.sep + root_object.name, root_object.name, root_object.matrix_world)
        export_success = _pip.export(*in_args)

    # PIS, PIA
    if root_object.scs_props.scs_root_animated == 'anim':
        # EXPORT PIS
        if scs_globals.export_pis_file and len(used_bones) > 0 and export_success:
            export_success = _pis.export(os.path.join(dirpath, skeleton_filepath), root_object, armature_object, list(used_bones.keys()))

        # EXPORT PIA
        if scs_globals.export_pia_file and len(used_bones) > 0 and export_success:

            anim_dirpath = _path_utils.get_animations_relative_filepath(root_object, dirpath)

            if anim_dirpath is not None:

                anim_dirpath = os.path.join(dirpath, anim_dirpath)
                # make sure to get relative path from PIA to PIS (animations may use custom export path)
                skeleton_filepath = _path_utils.get_skeleton_relative_filepath(armature_object, anim_dirpath, root_object.name)

                for scs_anim in root_object.scs_object_animation_inventory:

                    if scs_anim.export:  # check if export is disabled on animation itself

                        # TODO: use used_bones variable for safety checks
                        _pia.export(root_object, armature_object, scs_anim, anim_dirpath, skeleton_filepath)

            else:
                lprint("E Custom animations export path is not relative to SCS Project Base Path.\n\t   " +
                       "Animations won't be exported!")

    # FINAL FEEDBACK
    context.window.cursor_modal_restore()
    if export_success:
        lprint('\nI Export compleeted in %.3f sec. Files were saved to folder:\n\t   %r\n', (time.time() - t, dirpath))

    return True
