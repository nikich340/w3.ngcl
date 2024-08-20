

class Position():
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

class Quaternion():
    def __init__(self, x=0, y=0, z=0, w=1):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

class Scale():
    def __init__(self, x=1, y=1, z=1):
        self.x = x
        self.y = y
        self.z = z

class ReTransform():
    def __init__(self):
        self.position = Position()
        self.rotation = Quaternion()
        self.scale = Scale()
        self.matrix = None

    def to_float_list() -> list:
        pass

class ReKeyframe():
    def __init__(self):
        self.value = 0.0

class ReNode():
    def __init__(self):
        self.name = None
        self.transform = ReTransform()
        self.parent = None
        self.children = []
        self.attrs = {}

    def get_attr(self, name):
        return self.attrs[name] if name in self.attrs else None

    def set_attr(self, name, value):
        self.attrs[name] = value

    def get_children(self) -> list:
        return self.children

class ReBoneNode(ReNode):
    def __init__(self):
        super().__init__()

class ReSkeletonNode():
    def __init__(self):
        self.root = ReBoneNode()

class ReAssetDescription():
    def __init__(self):
        self.skeleton = ReSkeletonNode()

class ReKeyframeQt():
    def __init__(self):
        self.value = 0

class ReAnimationCurve():
    def __init__(self, re_transform: ReTransform):
        self.value = re_transform

class ReAnimationCurveContainer():
    def __init__(self):
        self.keyframes_qts = []

    def add_keyframe(self, re_keyframe: ReKeyframe):
        self.keyframes_qts.append(re_keyframe)

    def add_transformation(self, re_transform: ReTransform):
        anim_curve = ReAnimationCurve(re_transform)
        self.keyframes_qts.append(anim_curve)

    def set_keyframes_qts(self, keyframes_qts: list):
        self.keyframes_qts = keyframes_qts

class ReAnimationClip():
    def __init__(self):
        self.__curve_names = {}

    def add_curve(self, name) -> ReAnimationCurveContainer:
        self.__curve_names[name] = ReAnimationCurveContainer()
        return self.__curve_names[name]

    def get_curves_names(self):
        return self.__curve_names

    def get_animation_curve(self, curve_name) -> ReAnimationCurveContainer:
        return self.__curve_names[curve_name] if curve_name in self.__curve_names else None

class ReAnimationClipContainer():
    def __init__(self):
        self.animation_clip = ReAnimationClip()

class ReAnimationContainer():
    def __init__(self):
        self.animations = []

    def add_animation(self, animation):
        self.animations.append(animation)

    def add_animation_clip(self) -> ReAnimationClip:
        anim_clip = ReAnimationClipContainer()
        self.animations.append(anim_clip)
        return anim_clip.animation_clip

class ReShapeKeyContainer():
    def __init__(self):
        self.shape_keys = []

class ReAssetNode():
    def __init__(self):
        self.asset_description = ReAssetDescription()
        self.animation_container = ReAnimationContainer()
        self.shape_key_container = ReShapeKeyContainer()
        self.anim_length = 1.0
