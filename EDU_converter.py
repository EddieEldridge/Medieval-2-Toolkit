import bpy
import sys
import random
import re
import pickle
from pathlib import Path
from . import IK_2H, IK_Archer, IK_Dwarf, render_setup

script_folder = Path(__file__).parent

with open(script_folder/('2H_IK_skeletons.txt'), 'r', encoding="utf8") as TwoH:
    lines = TwoH.readlines()
    Controller_2H = [line.rstrip() for line in lines]
with open(script_folder/('Dwarf_IK_skeletons.txt'), 'r', encoding="utf8") as Dwarf:
    lines = Dwarf.readlines()
    Controller_Dwarf = [line.rstrip() for line in lines]
with open(script_folder/('Archer_IK_skeletons.txt'), 'r', encoding="utf8") as Archer:
    lines = Archer.readlines()
    Controller_Archer = [line.rstrip() for line in lines]


def mod_reader(mod_folder):
    #import_faction = "spain"
    master_dictionary = unit_reader(mod_folder)
    sort_factions(mod_folder)
    results = sort_bmdb(mod_folder)
    model_list = results[0]
    bmdb_list = results[1]
    master_dictionary = find_model(master_dictionary, bmdb_list, model_list)
    with open(script_folder/('text/master_dictionary.pkl'), 'wb') as master_output:
        pickle.dump(master_dictionary, master_output)


def unit_reader(mod_folder):
    # open edu
    with open((str(mod_folder)+"export_descr_unit.txt"), 'r', encoding="utf8") as edu:
        lines = edu.readlines()
        edu_lines = [line.rstrip() for line in lines if line[0] != ';']
    # open dmount
    with open((mod_folder+'descr_mount.txt'), 'r', encoding="utf8") as mount:
        lines = mount.readlines()
        mount_lines = [line.rstrip() for line in lines if line[0] != ';']
    master_dictionary = []
    unit_name = "sample_name"
    unit_mount = ["sample_mount"]
    unit_model = ["sample_model"]
    unit_owners = ["sample_faction"]
    unit_card_dir = ["sample_folder"]
    flag = 0
    # if dictionary line, start a new group
    for line in edu_lines:
        if("dictionary" in line):
            unit_dictionary = {"name": unit_name, "mount": unit_mount, "model": unit_model, "factions": unit_owners, "card": unit_card_dir}
            master_dictionary.append(unit_dictionary)
            unit_name = "missing"
            unit_mount = ["missing"]
            unit_model = []
            unit_owners = ["missing"]
            unit_card_dir = []
            riders = []
            flag = 0
            unit_name = line.split()[1]
        # if mount line, search for the mount name and get model
        elif("mount" in line.split()):
            unit_mount = [line.split(maxsplit = 1)[1]]
            x = 1
            flag = 0
            rider_amount = 0
            for line in mount_lines:
                if("type" in line and unit_mount[0].lower() in line.lower() and flag == 0):
                    flag = 1
                elif("model" in line and flag == 1):
                    unit_mount = [line.split()[1]]
                    flag = 2
                # get rider offsets
                elif("rider_offset" in line and flag == 2):
                    rider_offset = line.replace(",", "").split()[1:4]
                    riders.append(rider_offset)
                elif("type" in line and flag == 2):
                    unit_mount.append(riders)
                    flag = 0
                    break
            if(flag == 2 and riders != []):
                unit_mount.append(riders)
                flag = 0
        # if armour upgrade models line, get the last entry as the model name
        elif("armour_ug_models" in line):
            unit_model = line.replace(",", "").split()[1:]
        # if era 0 line, get all the entries as owners
        elif("era 0" in line):
            unit_owners = line.replace(",", "").split()[2:]
        #  if card_pic_dir line, get the entry to use in the image output directory
        elif("card_pic_dir" in line):
            flag = 1
            unit_card_dir.append(line.split()[1])
        elif("recruit_priority_offset" in line and flag != 1):
            unit_card_dir = unit_owners
    unit_dictionary = {"name": unit_name, "mount": unit_mount, "model": unit_model, "factions": unit_owners, "card": unit_card_dir}
    master_dictionary.append(unit_dictionary)
    return(master_dictionary)


def sort_factions(mod_folder):
    # write a list of factions
    available_factions_list = []
    with open((mod_folder+'descr_sm_factions.txt'), 'r', encoding="utf8") as edu:
        lines = edu.readlines()
        descr_sm_factions = [line.rstrip() for line in lines if line[0] != ';']
    for line in descr_sm_factions:
        if ("faction" in line.split()):
            line = line.split()[-1]
            available_factions_list.append(line)
    with open(script_folder/('text/available_factions.pkl'), 'wb') as available_factions_output:
        pickle.dump(available_factions_list, available_factions_output)
    return("Finished")


def sort_bmdb(mod_folder):
    # read descr_skeleton and bmdb into lists. 
    skeletons_list = []
    with open((mod_folder+'descr_skeleton.txt'), 'r', encoding="utf8") as skeleton:
        lines = skeleton.readlines()
        skeletons_list = [line.split()[-1] for line in lines if "type" in line.split()]
    with open((mod_folder+'unit_models/battle_models.modeldb'), 'r', encoding="utf8") as bmdb:
        lines = bmdb.readlines()
        bmdb_lines = [line.rstrip() for line in lines]
    # get model, factions, textures and skeleton
    model_list = []
    model = ""
    factions = []
    mains = []
    attach = []
    skeltype = ""
    flag = 0
    for line in bmdb_lines:
        if(flag == 0 and ".mesh" in line.lower()):
            model_info = [model, factions, skeltype]
            print(model_info)
            model_list.append(model_info)
            model = ""
            factions = []
            mains = []
            attach = []
            model = re.sub(".*/|\.mesh.*", "", line)+".dae"
            flag = 1
        elif(flag == 1 and ".texture" in line):
            if([previous_line.split()[1]] in factions):
                attach_texture = [re.sub(".*/|\.texture.*", "", line)+".dds"]
                n = 2
            else:
                factions.append([previous_line.split()[1]])
                main_texture = [re.sub(".*/|\.texture.*", "", line)+".dds"]
                n = 1
            flag = 2
        elif(flag == 2 and ".texture" in line):
            if(n == 2):
                attach_texture.append(re.sub(".*/|\.texture.*", "", line)+".dds")
                attach.append(attach_texture)
            else:
                main_texture.append(re.sub(".*/|\.texture.*", "", line)+".dds")
                mains.append(main_texture)
            flag = 1
        #If registered skeleton on line, save it and materials
        elif(any(x in line.split() for x in skeletons_list) and flag != 0):
            skeltype = line.split()[1]
            flag = 0
            count = 0
            for count, x in enumerate(factions):
                if(n==2):
                    x += mains[count]+attach[count]
                elif(n==1):
                    x += mains[count]
        #If no skeleton found but a new mesh line:
        elif(flag != 0 and ".mesh" in line.lower() and ".mesh" not in previous_line):
            print("No skeleton found for %s in descr_skeleton." % model)
            skeltype = "Missing Skeleton"
            count = 0
            for count, x in enumerate(factions):
                if(n==2):
                    x += mains[count]+attach[count]
                elif(n==1):
                    x += mains[count]
            model_info = [model, factions, skeltype]
            print(model_info)
            model_list.append(model_info)
            model = ""
            factions = []
            mains = []
            attach = []
            model = re.sub(".*/|\.mesh.*", "", line)+".dae"
            flag = 1
        previous_line = line
    model_info = [model, factions, skeltype]
    print(model_info)
    model_list.append(model_info)
    return(model_list, bmdb_lines)


def find_model(master_dictionary, bmdb_list, model_list):
    # search for model name in the line
    for unit in master_dictionary:
        for count, x in enumerate(unit['model']):
            print(unit['model'][count])
            flag = 0
            for line in bmdb_list:
                if(unit['model'][count].lower() in line.lower().split() and "/" not in line):
                    flag = 1
                elif(flag == 1 and ".mesh" in line):
                    unit['model'][count] = re.sub(".*/|.mesh.*", "", line)+".dae"
                    break
            for line in model_list:
                if(unit['model'][count] == line[0]):
                    unit['model'][count] = line
                    break
        for line in bmdb_list:
            if(unit["mount"][0] != "missing" and unit["mount"][0].lower() in line.lower() and "/" not in line):
                flag = 2
            elif(flag == 2 and ".mesh" in line):
                unit["mount"][0] = re.sub(".*/|.mesh.*", "", line)+".dae"
                break
        for line in model_list:
            if(unit["mount"][0] == line[0]):
                unit["mount"][0] = line
                break
    # for entry in master_dictionary:
    #     flag = 0
    #     for line in bmdb_list:
    #         if(entry["model"][0].lower() in line.lower().split() and "/" not in line):
    #             flag = 1
    #         elif(flag == 1 and ".mesh" in line):
    #             entry["model"][0] = re.sub(".*/|.mesh.*", "", line)+".dae"
    #             break
    #     for line in bmdb_list:
    #         if(entry["mount"][0] != "missing" and entry["mount"][0].lower() in line.lower() and "/" not in line):
    #             flag = 2
    #         elif(flag == 2 and ".mesh" in line):
    #             entry["mount"][0] = re.sub(".*/|.mesh.*", "", line)+".dae"
    #             break
    #     # Search the model from the list and append the texture info
    #     for line in model_list:
    #         if(entry["model"][0] == line[0]):
    #             entry["model"][0] = line
    #             break
    #     for line in model_list:
    #         if(entry["mount"][0] == line[0]):
    #             entry["mount"][0] = line
    #             break
        print(unit)
    return(master_dictionary)


def importer(model_folder, import_faction, x ,y ,z, upg_target):
    #Check for camera collection. Create if missing
    test = bpy.data.collections.get("Camera")
    if test == None:
        new_col = bpy.data.collections.new("Camera")
        bpy.context.scene.collection.children.link(new_col)
    #Check if faction has a collection. Create if not
    test = bpy.data.collections.get(import_faction)
    if test == None:
        new_col = bpy.data.collections.new(import_faction)
        bpy.context.scene.collection.children.link(new_col)
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]
        print("New collection")
    imported_units = []
    with open(script_folder/('text/master_dictionary.pkl'), 'rb') as master_input:
        master_dictionary = pickle.load(master_input)
    for entry in master_dictionary:
        if any (owner == import_faction for owner in entry["factions"]):
            print(entry)
            if entry['mount'][0] != "missing":
                if  mount_importer(model_folder, entry, import_faction, x, y, z, upg_target) == 2:
                    x += 2
                    imported_units.append(entry)
            elif entry['mount'][0] == "missing":
                if infantry_importer(model_folder, entry, import_faction, x, y, z, upg_target) == 2:
                    x+= 2
                    imported_units.append(entry)
    with open(script_folder/('text/imported_units.pkl'), 'wb') as imported_units_output:
        pickle.dump(imported_units, imported_units_output)
    print("Succesfully imported", int(x/2), "units.\n")
    render_setup.render_setup(model_folder)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection


def single_importer(model_folder, import_faction, import_unit, x ,y ,z, upg_target):
    with open(script_folder/('text/master_dictionary.pkl'), 'rb') as master_input:
        master_dictionary = pickle.load(master_input)
    for entry in master_dictionary:
        if import_unit == entry["name"]:
            if entry['mount'][0] != "missing":
                if  mount_importer(model_folder, entry, import_faction, x, y, z, upg_target) == 2:
                    x += 2
            elif entry['mount'][0] == "missing":
                if infantry_importer(model_folder, entry, import_faction, x, y, z, upg_target) == 2:
                    x+= 2
            break
    if x >0: print("Succesfully imported", import_unit)


def infantry_importer(folder, dae_model, import_faction, x, y, z, upg_target):
    print(dae_model)
    texture_path = folder+('textures/')
    #Define keywords
    try:
        model = dae_model['model'][upg_target][0]
    except IndexError:
        upg_target = len(dae_model['model'])-1
        model = dae_model['model'][upg_target][0]
    texture_flag = 0
    for entry in dae_model['model'][upg_target][1]:
        print(entry)
        if entry[0] == import_faction:
            main_texture = entry[1]
            main_normal = entry[2]
            texture_flag = 1
            break
        elif texture_flag == 0:
            main_texture = entry[1]
            main_normal = entry[2]
    #Print line if model doesn't exist
    file_check = Path(str(folder)+model)
    if not file_check.exists():
        print("No model file found:\n"+model)
        return(0)
    else:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        #Import .dae files, rename armatures and move the new objects
        bpy.ops.wm.collada_import(filepath=(folder+model))
        armature = bpy.data.objects["Armature"]
        armature.name = model.replace("_lod0.dae", "")
        armature.location = (x, y, z)
        #generate IK controls if defined
        try:
            IKType = dae_model['model'][upg_target][2]
            if IKType in Controller_2H:
                obj_controller = IK_2H.IKGenerator(armature.name, x, y, z)
                transfer_armature(armature, obj_controller)
                armature.parent = obj_controller
                armature.matrix_parent_inverse = obj_controller.matrix_world.inverted()
            elif IKType in Controller_Archer:
                obj_controller = IK_Archer.IKGenerator(armature.name, x, y, z)
                transfer_armature(armature, obj_controller)
                armature.parent = obj_controller
                armature.matrix_parent_inverse = obj_controller.matrix_world.inverted()
            elif IKType in Controller_Dwarf:
                obj_controller = IK_Dwarf.IKGenerator(armature.name, x, y, z)
                transfer_armature(armature, obj_controller)
                armature.parent = obj_controller
                armature.matrix_parent_inverse = obj_controller.matrix_world.inverted()
            else:
                print("Undefined IK type. Accepted types are: IK_1H, IK_2H and IK_Archer")
        except (ValueError,IndexError):
            print("NO IK defined")
        
        #Check material name to determine texture mode. Rename materials
        if "characterlod1__main" in bpy.data.materials:
            material = bpy.data.materials.get("characterlod1__main")
            material.name = ("characterlod0__main")
        if "characterlod2__main" in bpy.data.materials:
            material = bpy.data.materials.get("characterlod2__main")
            material.name = ("characterlod0__main")
        material = bpy.data.materials.get("characterlod0__main")
        if material != None:
            #Test whenever a texture is already in use
            result = check_existing_materials(material, main_texture)
            #If not, create a new material
            if result == "False":
                material.name = main_texture.replace(".dds", "")
                material_workflow(texture_path, model, main_texture, main_normal, material)
            texture_flag = 0
            for entry in dae_model['model'][upg_target][1]:
                if entry[0] == import_faction:
                    attachment_texture = entry[3]
                    attachment_normal = entry[4]
                    texture_flag = 1
                    break
                elif texture_flag == 0:
                    attachment_texture = entry[1]
                    attachment_normal = entry[2]
            if "characterlod1__attach" in bpy.data.materials:
                attachment_material = bpy.data.materials.get("characterlod1__attach")
                attachment_material.name = ("characterlod0__attach")
            if "characterlod2__attach" in bpy.data.materials:
                attachment_material = bpy.data.materials.get("characterlod2__attach")
                attachment_material.name = ("characterlod0__attach")
            attachment_material = bpy.data.materials["characterlod0__attach"]
            result = check_existing_materials(attachment_material, attachment_texture)
            if result == "False":
                attachment_material.name = attachment_texture.replace(".dds", "")
                material_workflow(texture_path, model, attachment_texture, attachment_normal, attachment_material)
        else:
            material = bpy.data.materials.get("characterlod0__single")
            if material != None:
                material.name = main_texture.replace(".dds", "")
                material_workflow(texture_path, model, main_texture, main_normal, material)
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        hide_variations()
        multi_textured_check()
        return(2)


def mount_importer(folder, dae_model, import_faction, x, y, z, upg_target):
    texture_path = folder+('textures/')
    #Define keywords
    mount = dae_model['mount'][0][0]
    texture_flag = 0
    for entry in dae_model['mount'][0][1]:
        print(entry)
        if entry[0] == import_faction:
            main_texture = entry[1]
            main_normal = entry[2]
            texture_flag = 1
            break
        elif texture_flag == 0:
            main_texture = entry[1]
            main_normal = entry[2]
    #Print line if model doesn't exist
    file_check = Path(str(folder)+mount)
    if not file_check.exists():
        print("No mount file found:\n"+mount)
        return(0)
    else:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        #Import .dae files, rename armatures and move the new objects
        bpy.ops.wm.collada_import(filepath=(folder+mount))
        armature = bpy.data.objects["Armature"]
        armature.name = mount.replace("_lod0.dae", "")
        armature.location = (x, y, z)
        
        #Check material name to determine texture mode. Rename materials
        material = bpy.data.materials.get("characterlod0__main")
        if material != None:
            #Test whenever a texture is already in use
            result = check_existing_materials(material, main_texture)
            #If not, create a new material
            if result == "False":
                material.name = main_texture.replace(".dds", "")
                material_workflow(texture_path, mount, main_texture, main_normal, material)
            texture_flag = 0
            for entry in dae_model['mount'][0][1]:
                if entry[0] in import_faction:
                    attachment_texture = entry[3]
                    attachment_normal = entry[4]
                    texture_flag = 1
                    break
                elif texture_flag == 0:
                    attachment_texture = entry[1]
                    attachment_normal = entry[2]
            attachment_material = bpy.data.materials["characterlod0__attach"]
            result = check_existing_materials(attachment_material, attachment_texture)
            if result == "False":
                attachment_material.name = attachment_texture.replace(".dds", "")
                material_workflow(texture_path, mount, attachment_texture, attachment_normal, attachment_material)
        else:
            material = bpy.data.materials.get("characterlod0__single")
            if material != None:
                material.name = main_texture.replace(".dds", "")
                material_workflow(texture_path, mount, main_texture, main_normal, material)
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        hide_variations()
        multi_textured_check()
        for rider in dae_model['mount'][1]:
            infantry_importer(folder, dae_model, import_faction, x+float(rider[0]), y+float(rider[2]), z+float(rider[1]), upg_target)
        return(2)


def check_existing_materials(current_material, material_name):
    #Test whenever a material is already in use, if not, rpoceed to material setup. If it already exists, replace the current material with the exisiting one
    seach_material = bpy.data.materials.get(material_name.replace(".dds", ""))
    if seach_material == None:
        print("Material doesn't exists: creating")
        return("False")
    else:
        model = find_first_object(current_material)
        print(model)
        if model != "None":
            model.select_set(True)
            bpy.context.view_layer.objects.active = model
            bpy.ops.object.select_linked(type='MATERIAL')
            model.data.materials[0] = seach_material
            bpy.ops.object.make_links_data(type='MATERIAL')
            return("True")


def find_first_object(current_material):
    #Find the first object which uses the current material, then return the object
    bpy.ops.object.select_all(action='DESELECT')
    for model in bpy.data.objects:
        #Only proceed if object is a mesh
        if model.type == 'MESH':
            if model.data.materials[0] == current_material:
                return(model)
    return("None")


def material_workflow(texture_path, model, texture, normal_texture, material):
    #Setup material mode and keywords
    material.use_nodes = True
    material.blend_method = 'CLIP'
    material.use_backface_culling = True
    nodes = material.node_tree.nodes
    new_link = material.node_tree.links.new
    
    #Defining nodes
    shader_node = material.node_tree.nodes["Principled BSDF"]
    
    texture_image = nodes.new("ShaderNodeTexImage")
    texture_image.location = (-506, 444)
    #Check if texture file doesn't exist
    file_check = Path(texture_path+texture)
    if not file_check.exists():
        print("No texture file found;", texture)
    else:
        print("Image found")
        texture_image.image = bpy.data.images.load(texture_path+texture)
    
    normal_image = nodes.new("ShaderNodeTexImage")
    normal_image.location = (-836, 124)
    #Check if texture file doesn't exist
    file_check = Path(texture_path+normal_texture)
    if not file_check.exists():
        print("No texture file found:", normal_texture)
    else:
        normal_image.image = bpy.data.images.load(texture_path+normal_texture)
        normal_image.image.colorspace_settings.name = 'Non-Color'
    
    rgb_curve = nodes.new("ShaderNodeRGBCurve")
    rgb_curve.location = (-506, 124)
    #Flip the green channel
    curve_g = rgb_curve.mapping.curves[1]
    curve_g.points[0].location = (0, 1)
    curve_g.points[1].location = (1, 0)
    
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.location = (-206, 124)

    #Linking nodes: colour -> shader; alpha -> shader; normal -> curves -> normal map -> shader
    new_link(shader_node.inputs[0], texture_image.outputs[0])
    new_link(shader_node.inputs[4], texture_image.outputs[1])
    new_link(rgb_curve.inputs[1], normal_image.outputs[0])
    new_link(normal_map.inputs[1], rgb_curve.outputs[0])
    new_link(shader_node.inputs[5], normal_map.outputs[0])


#Add "Copy Transfer" constraint to all bones
def transfer_armature(armature, obj_controller): 
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode='POSE',toggle=True)
    bpy.ops.pose.select_all(action='SELECT')
    for selected_bone in bpy.context.selected_pose_bones:
        if any(x in selected_bone.name for x in ["weapon", "Weapon"]):
            print("Skipping weapon bone")
        else:
            modifier = selected_bone.constraints.new("COPY_TRANSFORMS")
            modifier.target = obj_controller
            modifier.subtarget = selected_bone.name
            modifier.target_space = "LOCAL_WITH_PARENT"
            modifier.owner_space = "LOCAL_WITH_PARENT"
    bpy.ops.object.mode_set(mode='OBJECT',toggle=True)


#Check the comments of the model names and hide variations
def hide_variations():
    for parent_object in bpy.context.selected_objects:
        #Unhide all
        for obj in parent_object.children_recursive:
            obj.hide_render = False
            obj.hide_set(False)
        parent_object.select_set(True)
        list_of_names = []
        n = 0
        #Compare the object comment to the list of comments, if it's already registered, hide the current object
        obj_list = [x for x in parent_object.children_recursive]
        random.shuffle(obj_list)
        for obj in obj_list:
            object_group = obj.name.split("__")
            if object_group[0] in list_of_names:
                obj.hide_render = True
                obj.hide_set(True)
            else:
                list_of_names.append(object_group[0])
            #Hide secondaries and passives
            if any(x in obj.name for x in ["secondary", "passive"]):
                obj.hide_render = True
                obj.hide_set(True)


#Rename materials if object has more than
def multi_textured_check():
    #Compare the object comment to the list of comments, if it's already registered, hide the current object
    parent_object = bpy.context.view_layer.objects.active
    obj_list = [x for x in parent_object.children_recursive]
    random.shuffle(obj_list)
    for obj in obj_list:
        if obj.type == 'MESH' and len(obj.data.materials) > 1:
            for mat in obj.material_slots:
                mat.material.name = mat.material.name+"_suffix"
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def renderer():
    #Read the list of imported units to use as file names
    with open(script_folder/('text/imported_units.pkl'), 'rb') as imported_units_input:
        imported_units = pickle.load(imported_units_input)
    bpy.ops.object.select_all(action='DESELECT')
    #Check if camera controller exists. If not, create controller and camera
    controller = bpy.context.scene.objects.get("Camera Controller")
    if controller:
        #Select the camera controller and reset the position
        bpy.context.view_layer.objects.active = controller
        controller.select_set(True)
        bpy.context.scene.render.use_stamp_frame = False
        controller.location[0] = 0
        #Rename the output file, render and move the camera to the next unit
        for item in imported_units:
            bpy.data.scenes["Scene"].node_tree.nodes["File Output"].file_slots[0].path = ("#%s_#.tga" % item["name"])
            bpy.ops.render.render(use_viewport=True)
            bpy.ops.transform.translate(value=(2, 0, 0))
        #Reset camera location and output name
        controller.location[0] = 0
        bpy.data.scenes["Scene"].node_tree.nodes["File Output"].file_slots[0].path = ("")
