import h5py

with h5py.File('all_mimics.re', 'a') as fw:
    w_re_anim_clip = fw['.re_asset_node']['.re_animation_container']['.re_animation']['.re_anim_clip']
    with h5py.File('test_all_mimics.re', 'r') as fp:
        re_anim_clip = fp['.re_asset_node']['.re_animation_container']['.re_animation']['.re_anim_clip']
        for key in re_anim_clip:
            xformframes = re_anim_clip[key]['xformframes']
            del w_re_anim_clip[key]['xformframes']

            cut_xformframes = xformframes[35:233]
            if key == 'neck' or key == 'head' or key == 'hroll':
                cut_xformframe = xformframes[25]
                for i in range(len(cut_xformframes)):
                    cut_xformframes[i] = cut_xformframe

            w_re_anim_clip[key]['xformframes'] = cut_xformframes
