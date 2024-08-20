import h5py, math, os, shutil
import numpy, mathutils
if os.path.exists(__name__ + '.py'):
    from  install_dependecies import install_dependency
    from  common_data import CommonData
    from  asset_node import *
else:
    from .install_dependecies import install_dependency
    from .common_data import CommonData
    from .asset_node import *


class HdfManager():
    RE_NUMBONES_ATTR_NAME   = ".numbones"
    RE_NUMKEYS_ATTR_NAME    = ".numkeys"
    RE_LENGTH_ATTR_NAME     = ".animlength"

    RE_CURVE_LEN_ATTR_NAME      = ".curvelen"
    RE_NUM_CHANNELS_ATTR_NAME   = ".numchannels"
    RE_NUM_KEYS_ATTR_NAME       = ".numkeys"

    RE_SKEL_BONE_NAMES      = "bonenames"

    input_filename = None

    def __init__(self):
        self.nodes = []

    def read_hdf_file(self, filename):
        self.input_filename = filename
        with h5py.File(filename, 'r') as fp:
            for key in fp.keys():
                if key == '.re_asset_node':
                    self.parse_re_asset_node(fp)

    def write_hdf_file(self, filename, anim_node):
        while len(filename) < 1024:
            try:
                with h5py.File(filename, 'a') as fw:
                    break
            except:
                fname, ext = os.path.splitext(filename)
                filename = fname + CommonData.append_file_name + ext

        self.input_filename = None

        if self.input_filename:
            with h5py.File(self.input_filename, 'r') as fp:
                self.write_hdf_file_inner(filename, anim_node, fp)
        else:
            self.write_hdf_file_inner(filename, anim_node)

    def open_or_create_group_path(self, fw, path, delim = '/'):
        groups = path.split(delim)
        for group in groups:
            if group not in fw:
                fw = fw.create_group(group)
            else:
                fw = fw[group]
        return fw

    def write_hdf_file_inner(self, filename, anim_node, fp = None):
        with h5py.File(filename, 'w') as fw:
            if fp:
                for key in fp.keys():
                    fp.copy(fp[key], fw, key)

            # --- Skeleton ---
            re_skeleton_data = self.open_or_create_group_path(fw, f'.re_asset_node/.re_asset_description_node/.re_skeleton')
            skeleton_root = anim_node.asset_description.skeleton.root
            anim_clip = anim_node.animation_container.animations[0].animation_clip

            bone_names = []
            for curve_name in anim_clip.get_curves_names():
                bone_names.append(curve_name)
            #if self.RE_SKEL_BONE_NAMES in re_skeleton_data:
            #    del re_skeleton_data[self.RE_SKEL_BONE_NAMES]
            #re_skeleton_data.create_dataset(self.RE_SKEL_BONE_NAMES, data=numpy.asarray(bone_names, dtype=h5py.string_dtype(encoding='ascii')))

            # Delete helper root bone if it exists
            '''if CommonData.helper_root_bone_name == skeleton_root.name:
                for child in skeleton_root.get_children():
                    if anim_clip.get_animation_curve(skeleton_root.name):
                        data = anim_clip.get_curves_names()
                        del data[skeleton_root.name]
                    skeleton_root = child
                    anim_node.asset_description.skeleton.root = skeleton_root
                    break'''

            CommonData.root_bone_name = skeleton_root.name
            if CommonData.root_bone_name not in re_skeleton_data:
                self.set_re_child_node(skeleton_root, re_skeleton_data)

            if CommonData.helper_root_bone_name in re_skeleton_data:
                self.write_re_skeleton_node(skeleton_root, re_skeleton_data[CommonData.helper_root_bone_name])
            else:
                self.write_re_skeleton_node(skeleton_root, re_skeleton_data[CommonData.root_bone_name])

            '''if CommonData.helper_root_bone_name in re_skeleton_data and len(re_skeleton_data[CommonData.helper_root_bone_name]) > 0:
                for name in re_skeleton_data[CommonData.helper_root_bone_name]:
                    if isinstance(re_skeleton_data[CommonData.helper_root_bone_name][name], h5py.Group):
                        CommonData.root_bone_name = name'''

            # --- Animation ---
            anim_hdf_node = self.open_or_create_group_path(fw, '.re_asset_node/.re_animation_container/.re_animation')
            re_anim_clip_data = self.open_or_create_group_path(anim_hdf_node, '.re_anim_clip')

            self.remove_duplicated_bones(re_skeleton_data, anim_clip, re_anim_clip_data)

            #re_skeleton_data = re_skeleton_data[CommonData.root_bone_name]
            #del re_anim_clip_data[CommonData.root_bone_name]

            anim_hdf_node.attrs[self.RE_NUMKEYS_ATTR_NAME] = len(anim_clip.get_animation_curve(CommonData.root_bone_name).keyframes_qts)
            anim_hdf_node.attrs[self.RE_NUMBONES_ATTR_NAME] = len(anim_clip.get_curves_names())
            anim_hdf_node.attrs[self.RE_LENGTH_ATTR_NAME] = anim_node.anim_length

            for curve_name in anim_clip.get_curves_names():
                if curve_name in re_anim_clip_data and isinstance(re_anim_clip_data[curve_name], h5py.Group):
                    h5node_group = re_anim_clip_data[curve_name]
                else:
                    h5node_group = re_anim_clip_data.create_group(curve_name)

                anim_curve = anim_clip.get_animation_curve(curve_name)
                if anim_curve is not None:
                    keyframes_qts = anim_curve.keyframes_qts
                    if isinstance(keyframes_qts[0].value, ReTransform):
                        self.write_re_anim_node(keyframes_qts, h5node_group)
                    elif isinstance(keyframes_qts[0], ReKeyframe):
                        self.write_re_keyframe_node(keyframes_qts, h5node_group)

            # --- Mimic data ---
            if len(anim_node.shape_key_container.shape_keys) > 0:
                curve_node = self.open_or_create_group_path(fw, '.re_curve_node')

                curves = []

                self.write_shape_key_data(anim_node.shape_key_container.shape_keys, curve_node, curves)

                curve_node.attrs[self.RE_CURVE_LEN_ATTR_NAME] = anim_node.anim_length
                curve_node.attrs[self.RE_NUM_CHANNELS_ATTR_NAME] = len(curves)
                curve_node.attrs[self.RE_NUM_KEYS_ATTR_NAME] = len(anim_clip.get_animation_curve(CommonData.root_bone_name).keyframes_qts)

    def get_nodes(self):
        return self.nodes

    def parse_re_asset_node(self, f):
        re_asset_node = ReAssetNode()

        # --- Skeleton ---
        re_skeleton_data = self.open_or_create_group_path(f, '.re_asset_node/.re_asset_description_node/.re_skeleton')
        for key in re_skeleton_data:
            if isinstance(re_skeleton_data[key], h5py.Group):
                node_data = re_asset_node.asset_description.skeleton.root
                node_data.name = key
                node_data.transform = self.parse_transform_list(re_skeleton_data[key]['.transform'])
                if '.attributes' in re_skeleton_data[key]:
                    for attr_data in re_skeleton_data[key]['.attributes']:
                        node_data.set_attr(attr_data[0].decode("utf-8"), attr_data[1])
                self.parse_re_group_node(re_skeleton_data[key], node_data)

        # --- Animation ---
        re_animation = self.open_or_create_group_path(f, '.re_asset_node/.re_animation_container/.re_animation')
        if self.RE_LENGTH_ATTR_NAME in re_animation.attrs:
            re_asset_node.anim_length = re_animation.attrs[self.RE_LENGTH_ATTR_NAME]

        re_anim_clip_data = re_animation['.re_anim_clip']
        anim_clip = re_asset_node.animation_container.add_animation_clip()
        for key in re_anim_clip_data:
            if isinstance(re_anim_clip_data[key], h5py.Group):
                self.parse_re_anim_node(anim_clip, key, re_anim_clip_data[key])

        # --- Mimic data ---
        if '.re_curve_node' in f:
            re_curve_node = self.open_or_create_group_path(f, '.re_curve_node')
            self.parse_re_curve_node(re_asset_node, re_curve_node)

        self.nodes.append(re_asset_node)

    def parse_re_group_node(self, re_skeleton_data, re_node_data):
        for key in re_skeleton_data:
            if isinstance(re_skeleton_data[key], h5py.Group):
                new_node_data = ReBoneNode()
                new_node_data.parent = re_node_data
                new_node_data.name = key
                new_node_data.transform = self.parse_transform_list(re_skeleton_data[key]['.transform'])
                re_node_data.children.append(new_node_data)
                self.parse_re_group_node(re_skeleton_data[key], new_node_data)

    def parse_re_anim_node(self, anim_clip, name, re_anim_node):
        if 'xformframes' in re_anim_node:
            anim_curve = anim_clip.add_curve(name)
            for line in re_anim_node['xformframes']:
                if len(line) == 1:
                    line = line[0]
                transform = ReTransform()
                transform.position = Position(line[0], line[1], line[2])
                transform.rotation = Quaternion(line[3], line[4], line[5], line[6])
                transform.scale = Scale(line[7], line[8], line[9])
                anim_curve.add_transformation(transform)
        if 'keyframes' in re_anim_node:
            anim_curve = anim_clip.add_curve(name)
            for line in re_anim_node['keyframes']:
                keyframe = ReKeyframe()
                keyframe.value = line[0]
                anim_curve.add_keyframe(keyframe)

    def parse_re_curve_node(self, anim_node, re_curve_node):
        if 'tracknames' in re_curve_node and 'trackdata' in re_curve_node:
            tracknames = re_curve_node['tracknames']
            for line in re_curve_node['trackdata']:
                if len(line) == 1:
                    line = line[0]
                curr_shape_data = []
                for idx, val in enumerate(line):
                    if idx >= len(tracknames):
                        break
                    trackname = tracknames[idx]
                    if isinstance(trackname, numpy.ndarray) and len(trackname) > 0:
                        trackname = trackname[0]
                    if isinstance(trackname, bytes):
                        trackname = trackname.decode()
                    curr_shape_data.append({trackname: val})
                anim_node.shape_key_container.shape_keys.append(curr_shape_data)

    def init_absolute_root_bone_transformation(self, anim_clip, re_asset_node):
        root_node_data = re_asset_node.asset_description.skeleton.root

        new_node_data = ReBoneNode()
        new_node_data.name = CommonData.helper_root_bone_name

        vec = CommonData.unit_vector
        new_node_data.transform.position = Position(vec[0], vec[1], vec[2])
        new_node_data.transform.rotation = Quaternion()
        new_node_data.transform.scale = Scale()

        new_node_data.children.append(root_node_data)
        root_node_data.parent = new_node_data

        anim_curve = anim_clip.add_curve(new_node_data.name)
        for _ in range(len(anim_clip.get_animation_curve(root_node_data.name).keyframes_qts)):
            anim_curve.add_transformation(root_node_data.transform)

        re_asset_node.asset_description.skeleton.root = new_node_data

    def set_re_child_node(self, child, skeleton_node):
        transform = child.transform
        pos = transform.position
        re_skeleton_node_data = numpy.array([
            list([pos.x, pos.y, pos.z]) +
            list(self.quaternion_to_m33_list(transform.rotation))
        ])
        if child.name in skeleton_node:
            del skeleton_node[child.name]['.transform']
        else:
            skeleton_node.create_group(child.name)
        skeleton_node[child.name].create_dataset('.transform', data=re_skeleton_node_data)
        return skeleton_node[child.name]

    def remove_duplicated_bones(self, skeleton_root, anim_clip, anim_clip_data):
        unique_child_names = []
        for child in skeleton_root:
            if isinstance(skeleton_root[child], h5py.Group):
                if child in unique_child_names or child != CommonData.root_bone_name:
                    del skeleton_root[child]
                    if child in anim_clip_data:
                        del anim_clip_data[child]
                    if anim_clip.get_animation_curve(child):
                        data = anim_clip.get_curves_names()
                        del data[child]
                    continue
                unique_child_names.append(child)
        def parse_children(parent_node):
            for child in parent_node:
                if isinstance(parent_node[child], h5py.Group):
                    if child in unique_child_names:
                        del parent_node[child]
                        if child in anim_clip_data:
                            del anim_clip_data[child]
                        if anim_clip.get_animation_curve(child):
                            data = anim_clip.get_curves_names()
                            del data[child]
                        continue
                    unique_child_names.append(child)
                    parse_children(parent_node[child])
        parse_children(skeleton_root[CommonData.root_bone_name])

    def write_re_skeleton_node(self, skeleton_root, re_skeleton_node):
        def parse_children(node, parent_node):
            for child in node.children:
                skeleton_child_node = self.set_re_child_node(child, parent_node)
                parse_children(child, skeleton_child_node)
        parse_children(skeleton_root, re_skeleton_node)

    def write_re_anim_node(self, keyframes_qts, re_anim_node):
        time = 0.
        re_anim_node_data = []
        for keyframes_qt in keyframes_qts:
            re_transform = keyframes_qt.value
            pos, rot, scale = re_transform.position, re_transform.rotation, re_transform.scale 
            re_anim_node_data.append((
                pos.x, pos.y, pos.z,
                rot.x, rot.y, rot.z, rot.w,
                scale.x, scale.y, scale.z,
                time,
            ))
            time += 1.0
        headers = ['pos.x', 'pos.y', 'pos.z', 'rot.x', 'rot.y', 'rot.z', 'rot.w', 'scale.x', 'scale.y', 'scale.z', 'time']
        ds_dt = numpy.dtype({
            'names': headers,
            'formats': [('float32')]*len(headers),
        })
        re_anim_node_data = numpy.array(re_anim_node_data, dtype=ds_dt)
        if 'xformframes' in re_anim_node:
            del re_anim_node['xformframes']
        re_anim_node.create_dataset('xformframes', data=re_anim_node_data)

    def write_re_keyframe_node(self, keyframes_qts, re_anim_node):
        time = 0.
        re_keyframe_node_data = []
        for keyframes_qt in keyframes_qts:
            re_keyframe = keyframes_qt.value
            re_keyframe_node_data.append((
                re_keyframe,
                time,
            ))
            time += 1.0
        headers = ['value', 'time']
        ds_dt = numpy.dtype({
            'names': headers,
            'formats': [('float32')]*len(headers),
        })
        re_keyframe_node_data = numpy.array(re_keyframe_node_data, dtype=ds_dt)
        del re_anim_node['keyframes']
        re_anim_node.create_dataset('keyframes', data=re_keyframe_node_data)

    def write_shape_key_data(self, shape_keys, curve_node, headers):
        re_node_data = []

        for key_data in shape_keys:
            for key in key_data:
                headers.append(key)
            break

        for key_data in shape_keys:
            re_node_data_val = []
            for key in key_data:
                re_node_data_val.append(key_data[key])
            re_node_data.append(tuple(re_node_data_val))

        ds_dt = numpy.dtype({
            'names': headers,
            'formats': [('float32')]*len(headers),
        })

        re_node_data = numpy.array(re_node_data, dtype=ds_dt)

        data_name = 'trackdata'
        if data_name in curve_node:
            del curve_node[data_name]
        curve_node.create_dataset(data_name, data=re_node_data)

        data_name = 'tracknames'
        if data_name in curve_node:
            del curve_node[data_name]
        ascii_header = numpy.asarray(headers, dtype=h5py.string_dtype(encoding='ascii'))
        curve_node.create_dataset(data_name, data=ascii_header)

    def parse_transform_list(self, float_list: h5py.Dataset) -> ReTransform:
        fl = list(float_list[0])
        transform = ReTransform()
        transform.position = Position(fl[0], fl[1], fl[2])
        transform.rotation = self.m33_list_to_quaternion(fl)
        transform.scale = Scale(1, 1, 1)
        return transform

    def m33_list_to_quaternion(self, fl):
        mrow1x, mrow1y, mrow1z = fl[3], fl[4],  fl[5]
        mrow2x, mrow2y, mrow2z = fl[6], fl[7],  fl[8]
        mrow3x, mrow3y, mrow3z = fl[9], fl[10], fl[11]

        q0 = ( mrow1x + mrow2y + mrow3z + 1.) / 4.
        q1 = ( mrow1x - mrow2y - mrow3z + 1.) / 4.
        q2 = (-mrow1x + mrow2y - mrow3z + 1.) / 4.
        q3 = (-mrow1x - mrow2y + mrow3z + 1.) / 4.
        if q0 < 0.: q0 = 0.
        if q1 < 0.: q1 = 0.
        if q2 < 0.: q2 = 0.
        if q3 < 0.: q3 = 0.
        q0 = math.sqrt(q0)
        q1 = math.sqrt(q1)
        q2 = math.sqrt(q2)
        q3 = math.sqrt(q3)
        if q0 >= q1 and q0 >= q2 and q0 >= q3:
            q0 *= +1.
            q1 *= numpy.sign(mrow3y - mrow2z)
            q2 *= numpy.sign(mrow1z - mrow3x)
            q3 *= numpy.sign(mrow2x - mrow1y)
        elif q1 >= q0 and q1 >= q2 and q1 >= q3:
            q0 *= numpy.sign(mrow3y - mrow2z)
            q1 *= +1.
            q2 *= numpy.sign(mrow2x + mrow1y)
            q3 *= numpy.sign(mrow1z + mrow3x)
        elif q2 >= q0 and q2 >= q1 and q2 >= q3:
            q0 *= numpy.sign(mrow1z - mrow3x)
            q1 *= numpy.sign(mrow2x + mrow1y)
            q2 *= +1.
            q3 *= numpy.sign(mrow3y + mrow2z)
        elif q3 >= q0 and q3 >= q1 and q3 >= q2:
            q0 *= numpy.sign(mrow2x - mrow1y)
            q1 *= numpy.sign(mrow3x + mrow1z)
            q2 *= numpy.sign(mrow3y + mrow2z)
            q3 *= +1.

        q = mathutils.Quaternion()
        q.x = q1
        q.y = q2
        q.z = q3
        q.w = q0
        q.normalize()

        return q

    def quaternion_to_m33_list(self, q):
        fl = [
            1-(2*((q.y*q.y)+(q.z*q.z))), 2*((q.x*q.y)-(q.w*q.z)),     2*((q.w*q.y)+(q.x*q.z)),
            2*((q.x*q.y)+(q.w*q.z)),     1-(2*((q.x*q.x)+(q.z*q.z))), 2*((q.y*q.z)-(q.w*q.x)),
            2*((q.x*q.z)-(q.w*q.y)),     2*((q.y*q.z)+(q.w*q.x)),     1-(2*((q.x*q.x)+(q.y*q.y))),
        ]
        return fl
