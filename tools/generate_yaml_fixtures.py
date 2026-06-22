#!/usr/bin/env python3
"""
Deterministic, idempotent generator for the copyright-safe MiniDungeon demo fixture.

This is the OFFLINE reproduction path: it writes the Unity 6 serialized assets
(.mat / .prefab / .unity) and every .meta file directly, with a fully consistent
fileID / GUID graph. The in-editor reproduction path is
Assets/Demo/Editor/DemoAssetGenerator.cs (Tools/Demo/Regenerate MiniDungeon Demo).

It uses NO external assets: only Unity built-in primitive meshes, the built-in
URP/Lit shader (a package shader, not a downloaded asset), generated materials,
and repository C# scripts.

Run from the project root:
    python3 tools/generate_yaml_fixtures.py

GUIDs are derived deterministically as md5("demodungeon::<asset path>"), so re-running
produces identical files (idempotent).
"""

import hashlib
import os

# --------------------------------------------------------------------------- constants

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADER = "%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n"

DEFAULT_RES_GUID = "0000000000000000e000000000000000"   # built-in default resources (meshes)
URP_LIT_GUID = "933532a4fcc9baf4fa0491de14d08ed7"        # Universal Render Pipeline/Lit shader

MAT_MAIN_ID = 2100000
SHADER_MAIN_ID = 4800000
SCRIPT_MAIN_ID = 11500000

MESH = {"cube": 10202, "cylinder": 10206, "sphere": 10207, "capsule": 10208}


def guid(path):
    return hashlib.md5(("demodungeon::" + path).encode()).hexdigest()


def fnum(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    s = ("%f" % v).rstrip("0").rstrip(".")
    return s if s else "0"


def fvec3(v):
    return "{x: %s, y: %s, z: %s}" % (fnum(v[0]), fnum(v[1]), fnum(v[2]))


# --------------------------------------------------------------------------- asset table

ASSET_PATHS = [
    "Assets/Demo", "Assets/Demo/Scenes", "Assets/Demo/Prefabs", "Assets/Demo/Materials",
    "Assets/Demo/Scripts", "Assets/Demo/Editor", "Assets/Demo/Tests",
    "Assets/Demo/Tests/EditMode", "Assets/Demo/Tests/PlayMode",
    "Assets/Demo/Scripts/DemoTorch.cs", "Assets/Demo/Scripts/DemoDoor.cs",
    "Assets/Demo/Scripts/DemoRoomState.cs", "Assets/Demo/Scripts/DemoDummyTarget.cs",
    "Assets/Demo/Scripts/DemoBootstrap.cs", "Assets/Demo/Scripts/DemoDungeon.Runtime.asmdef",
    "Assets/Demo/Editor/DemoAssetGenerator.cs", "Assets/Demo/Editor/DemoDungeon.Editor.asmdef",
    "Assets/Demo/Tests/EditMode/DemoAssetIntegrityTests.cs",
    "Assets/Demo/Tests/EditMode/DemoDungeon.EditMode.Tests.asmdef",
    "Assets/Demo/Tests/PlayMode/MiniDungeonPlayModeTests.cs",
    "Assets/Demo/Tests/PlayMode/DemoDungeon.PlayMode.Tests.asmdef",
    "Assets/Demo/Materials/M_Stone.mat", "Assets/Demo/Materials/M_Wood.mat",
    "Assets/Demo/Materials/M_Torch_On.mat", "Assets/Demo/Materials/M_Torch_Off.mat",
    "Assets/Demo/Materials/M_Dummy.mat", "Assets/Demo/Materials/M_Door.mat",
    "Assets/Demo/Prefabs/Room_Start.prefab", "Assets/Demo/Prefabs/Room_Combat.prefab",
    "Assets/Demo/Prefabs/Door.prefab", "Assets/Demo/Prefabs/Torch.prefab",
    "Assets/Demo/Prefabs/DummyTarget.prefab", "Assets/Demo/Prefabs/PlayerSpawn.prefab",
    "Assets/Demo/Scenes/MiniDungeon.unity", "Assets/Demo/README.md",
]
G = {p: guid(p) for p in ASSET_PATHS}

SCRIPT = {name: G["Assets/Demo/Scripts/%s.cs" % name] for name in
          ["DemoTorch", "DemoDoor", "DemoRoomState", "DemoDummyTarget", "DemoBootstrap"]}
MAT = {name: G["Assets/Demo/Materials/%s.mat" % name] for name in
       ["M_Stone", "M_Wood", "M_Torch_On", "M_Torch_Off", "M_Dummy", "M_Door"]}


def mat_ref(name):
    return "{fileID: %d, guid: %s, type: 2}" % (MAT_MAIN_ID, MAT[name])


def script_ref(name):
    return "{fileID: %d, guid: %s, type: 3}" % (SCRIPT_MAIN_ID, SCRIPT[name])


# --------------------------------------------------------------------------- block emitters

def doc(classid, fileid, body):
    return "--- !u!%d &%d\n%s" % (classid, fileid, body)


def go_block(fileid, name, comp_ids, layer=0, tag="Untagged", active=1):
    if comp_ids:
        comps = "  m_Component:\n" + "".join("  - component: {fileID: %d}\n" % c for c in comp_ids)
    else:
        comps = "  m_Component: []\n"
    body = (
        "GameObject:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  serializedVersion: 6\n"
        + comps +
        "  m_Layer: %d\n" % layer +
        "  m_Name: %s\n" % name +
        "  m_TagString: %s\n" % tag +
        "  m_Icon: {fileID: 0}\n"
        "  m_NavMeshLayer: 0\n"
        "  m_StaticEditorFlags: 0\n"
        "  m_IsActive: %d\n" % active
    )
    return doc(1, fileid, body)


def transform_block(fileid, go_id, pos, scale, children, father, rot=(0, 0, 0, 1), euler=(0, 0, 0)):
    if children:
        ch = "  m_Children:\n" + "".join("  - {fileID: %d}\n" % c for c in children)
    else:
        ch = "  m_Children: []\n"
    body = (
        "Transform:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_GameObject: {fileID: %d}\n" % go_id +
        "  serializedVersion: 2\n"
        "  m_LocalRotation: {x: %s, y: %s, z: %s, w: %s}\n" % (fnum(rot[0]), fnum(rot[1]), fnum(rot[2]), fnum(rot[3])) +
        "  m_LocalPosition: %s\n" % fvec3(pos) +
        "  m_LocalScale: %s\n" % fvec3(scale) +
        "  m_ConstrainProportionsScale: 0\n"
        + ch +
        "  m_Father: {fileID: %d}\n" % father +
        "  m_LocalEulerAnglesHint: %s\n" % fvec3(euler)
    )
    return doc(4, fileid, body)


def meshfilter_block(fileid, go_id, mesh_id):
    body = (
        "MeshFilter:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_GameObject: {fileID: %d}\n" % go_id +
        "  m_Mesh: {fileID: %d, guid: %s, type: 0}\n" % (mesh_id, DEFAULT_RES_GUID)
    )
    return doc(33, fileid, body)


def meshrenderer_block(fileid, go_id, material_name):
    body = (
        "MeshRenderer:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_GameObject: {fileID: %d}\n" % go_id +
        "  m_Enabled: 1\n"
        "  m_CastShadows: 1\n"
        "  m_ReceiveShadows: 1\n"
        "  m_DynamicOccludee: 1\n"
        "  m_StaticShadowCaster: 0\n"
        "  m_MotionVectors: 1\n"
        "  m_LightProbeUsage: 1\n"
        "  m_ReflectionProbeUsage: 1\n"
        "  m_RayTracingMode: 2\n"
        "  m_RayTraceProcedural: 0\n"
        "  m_RayTracingAccelStructBuildFlagsOverride: 0\n"
        "  m_RayTracingAccelStructBuildFlags: 1\n"
        "  m_SmallMeshCulling: 1\n"
        "  m_ForceMeshLod: -1\n"
        "  m_MeshLodSelectionBias: 0\n"
        "  m_RenderingLayerMask: 1\n"
        "  m_RendererPriority: 0\n"
        "  m_Materials:\n"
        "  - %s\n" % mat_ref(material_name) +
        "  m_StaticBatchInfo:\n"
        "    firstSubMesh: 0\n"
        "    subMeshCount: 0\n"
        "  m_StaticBatchRoot: {fileID: 0}\n"
        "  m_ProbeAnchor: {fileID: 0}\n"
        "  m_LightProbeVolumeOverride: {fileID: 0}\n"
        "  m_ScaleInLightmap: 1\n"
        "  m_ReceiveGI: 1\n"
        "  m_PreserveUVs: 0\n"
        "  m_IgnoreNormalsForChartDetection: 0\n"
        "  m_ImportantGI: 0\n"
        "  m_StitchLightmapSeams: 1\n"
        "  m_SelectedEditorRenderState: 3\n"
        "  m_MinimumChartSize: 4\n"
        "  m_AutoUVMaxDistance: 0.5\n"
        "  m_AutoUVMaxAngle: 89\n"
        "  m_LightmapParameters: {fileID: 0}\n"
        "  m_GlobalIlluminationMeshLod: 0\n"
        "  m_SortingLayerID: 0\n"
        "  m_SortingLayer: 0\n"
        "  m_SortingOrder: 0\n"
        "  m_AdditionalVertexStreams: {fileID: 0}\n"
    )
    return doc(23, fileid, body)


def light_block(fileid, go_id, color=(1, 0.7, 0.35), intensity=1.5, rng=4):
    body = (
        "Light:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_GameObject: {fileID: %d}\n" % go_id +
        "  m_Enabled: 1\n"
        "  serializedVersion: 13\n"
        "  m_Type: 2\n"
        "  m_Color: {r: %s, g: %s, b: %s, a: 1}\n" % (fnum(color[0]), fnum(color[1]), fnum(color[2])) +
        "  m_Intensity: %s\n" % fnum(intensity) +
        "  m_Range: %s\n" % fnum(rng) +
        "  m_SpotAngle: 30\n"
        "  m_InnerSpotAngle: 21.802082\n"
        "  m_CookieSize2D: {x: 10, y: 10}\n"
        "  m_Shadows:\n"
        "    m_Type: 0\n"
        "    m_Resolution: -1\n"
        "    m_CustomResolution: -1\n"
        "    m_Strength: 1\n"
        "    m_Bias: 0.05\n"
        "    m_NormalBias: 0.4\n"
        "    m_NearPlane: 0.2\n"
        "    m_CullingMatrixOverride:\n"
        "      e00: 1\n      e01: 0\n      e02: 0\n      e03: 0\n"
        "      e10: 0\n      e11: 1\n      e12: 0\n      e13: 0\n"
        "      e20: 0\n      e21: 0\n      e22: 1\n      e23: 0\n"
        "      e30: 0\n      e31: 0\n      e32: 0\n      e33: 1\n"
        "    m_UseCullingMatrixOverride: 0\n"
        "  m_Cookie: {fileID: 0}\n"
        "  m_DrawHalo: 0\n"
        "  m_Flare: {fileID: 0}\n"
        "  m_RenderMode: 0\n"
        "  m_CullingMask:\n"
        "    serializedVersion: 2\n"
        "    m_Bits: 4294967295\n"
        "  m_RenderingLayerMask: 1\n"
        "  m_Lightmapping: 4\n"
        "  m_LightShadowCasterMode: 0\n"
        "  m_AreaSize: {x: 1, y: 1}\n"
        "  m_BounceIntensity: 1\n"
        "  m_ColorTemperature: 6570\n"
        "  m_UseColorTemperature: 0\n"
        "  m_BoundingSphereOverride: {x: 0, y: 0, z: 0, w: 0}\n"
        "  m_UseBoundingSphereOverride: 0\n"
        "  m_UseViewFrustumForShadowCasterCull: 1\n"
        "  m_ForceVisible: 0\n"
    )
    return doc(108, fileid, body)


def boxcollider_block(fileid, go_id, size, center=(0, 0, 0), trigger=1):
    body = (
        "BoxCollider:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_GameObject: {fileID: %d}\n" % go_id +
        "  m_Material: {fileID: 0}\n"
        "  m_IncludeLayers:\n    serializedVersion: 2\n    m_Bits: 0\n"
        "  m_ExcludeLayers:\n    serializedVersion: 2\n    m_Bits: 0\n"
        "  m_LayerOverridePriority: 0\n"
        "  m_IsTrigger: %d\n" % trigger +
        "  m_ProvidesContacts: 0\n"
        "  m_Enabled: 1\n"
        "  serializedVersion: 3\n"
        "  m_Size: %s\n" % fvec3(size) +
        "  m_Center: %s\n" % fvec3(center)
    )
    return doc(65, fileid, body)


def mono_block(fileid, go_id, script_name, fields_yaml):
    body = (
        "MonoBehaviour:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_GameObject: {fileID: %d}\n" % go_id +
        "  m_Enabled: 1\n"
        "  m_EditorHideFlags: 0\n"
        "  m_Script: %s\n" % script_ref(script_name) +
        "  m_Name: \n"
        "  m_EditorClassIdentifier: \n"
        + fields_yaml
    )
    return doc(114, fileid, body)


# --------------------------------------------------------------------------- material docs

def material_doc(name, base_color, smoothness, metallic=0.0):
    body = (
        "Material:\n"
        "  serializedVersion: 8\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_Name: %s\n" % name +
        "  m_Shader: {fileID: %d, guid: %s, type: 3}\n" % (SHADER_MAIN_ID, URP_LIT_GUID) +
        "  m_Parent: {fileID: 0}\n"
        "  m_ModifiedSerializedProperties: 0\n"
        "  m_ValidKeywords: []\n"
        "  m_InvalidKeywords: []\n"
        "  m_LightmapFlags: 4\n"
        "  m_EnableInstancingVariants: 0\n"
        "  m_DoubleSidedGI: 0\n"
        "  m_CustomRenderQueue: -1\n"
        "  stringTagMap: {}\n"
        "  disabledShaderPasses: []\n"
        "  m_LockedProperties: \n"
        "  m_SavedProperties:\n"
        "    serializedVersion: 3\n"
        "    m_TexEnvs:\n"
        "    - _BaseMap:\n"
        "        m_Texture: {fileID: 0}\n"
        "        m_Scale: {x: 1, y: 1}\n"
        "        m_Offset: {x: 0, y: 0}\n"
        "    m_Ints: []\n"
        "    m_Floats:\n"
        "    - _Metallic: %s\n" % fnum(metallic) +
        "    - _Smoothness: %s\n" % fnum(smoothness) +
        "    m_Colors:\n"
        "    - _BaseColor: {r: %s, g: %s, b: %s, a: 1}\n" % (fnum(base_color[0]), fnum(base_color[1]), fnum(base_color[2]))
    )
    return HEADER + doc(21, MAT_MAIN_ID, body)


MATERIALS = {
    "M_Stone": ((0.5, 0.5, 0.5), 0.1),
    "M_Wood": ((0.40, 0.26, 0.13), 0.1),
    "M_Torch_On": ((1.0, 0.55, 0.15), 0.3),
    "M_Torch_Off": ((0.20, 0.16, 0.12), 0.1),
    "M_Dummy": ((0.70, 0.22, 0.22), 0.2),
    "M_Door": ((0.30, 0.20, 0.12), 0.1),
}


# --------------------------------------------------------------------------- node tree

class Node:
    def __init__(self, name, key=None, prim=None, material=None, light=None, box=None,
                 monos=None, pos=(0, 0, 0), scale=(1, 1, 1), layer=0, tag="Untagged",
                 active=1, children=None):
        self.name = name
        self.key = key
        self.prim = prim
        self.material = material
        self.light = light            # None or dict of light params
        self.box = box                # None or dict {size, center, trigger}
        self.monos = monos or []      # list of dict {script, fields(callable|str)}
        self.pos = pos
        self.scale = scale
        self.layer = layer
        self.tag = tag
        self.active = active
        self.children = children or []
        # assigned during allocation:
        self.go = self.t = self.mf = self.mr = self.li = self.bc = None
        self.mono_ids = []


class Allocator:
    def __init__(self, start):
        self._n = start - 1

    def nid(self):
        self._n += 1
        return self._n


def allocate(node, alloc, reg):
    node.go = alloc.nid()
    node.t = alloc.nid()
    if node.prim:
        node.mf = alloc.nid()
        node.mr = alloc.nid()
    if node.light is not None:
        node.li = alloc.nid()
    if node.box is not None:
        node.bc = alloc.nid()
    node.mono_ids = [alloc.nid() for _ in node.monos]
    if node.key:
        reg[node.key] = node
    for c in node.children:
        allocate(c, alloc, reg)


def render(node, docs, father_id, reg):
    comp_ids = [node.t]
    if node.mf:
        comp_ids.append(node.mf)
    if node.mr:
        comp_ids.append(node.mr)
    if node.li:
        comp_ids.append(node.li)
    if node.bc:
        comp_ids.append(node.bc)
    comp_ids += node.mono_ids

    docs.append(go_block(node.go, node.name, comp_ids, node.layer, node.tag, node.active))
    docs.append(transform_block(node.t, node.go, node.pos, node.scale,
                                [c.t for c in node.children], father_id))
    if node.mf:
        docs.append(meshfilter_block(node.mf, node.go, MESH[node.prim]))
    if node.mr:
        docs.append(meshrenderer_block(node.mr, node.go, node.material))
    if node.li:
        docs.append(light_block(node.li, node.go, **node.light))
    if node.bc:
        docs.append(boxcollider_block(node.bc, node.go, **node.box))
    for i, m in enumerate(node.monos):
        fields = m["fields"](reg) if callable(m["fields"]) else m["fields"]
        docs.append(mono_block(node.mono_ids[i], node.go, m["script"], fields))
    for c in node.children:
        render(c, docs, node.t, reg)


def ref(fileid):
    return "{fileID: %d}" % fileid


# --------------------------------------------------------------------------- node factories

def torch_node(key_prefix, name, pos=(0, 0, 0)):
    flame_key = key_prefix + ".flame"
    light_key = key_prefix + ".light"

    def torch_fields(reg):
        return (
            "  startLit: 0\n"
            "  pointLight: %s\n" % ref(reg[light_key].li) +
            "  flameRenderer: %s\n" % ref(reg[flame_key].mr) +
            "  litMaterial: %s\n" % mat_ref("M_Torch_On") +
            "  unlitMaterial: %s\n" % mat_ref("M_Torch_Off")
        )

    return Node(
        name, key=key_prefix, pos=pos,
        monos=[{"script": "DemoTorch", "fields": torch_fields}],
        children=[
            Node("Base_Cylinder", prim="cylinder", material="M_Wood", pos=(0, 0.5, 0), scale=(0.2, 0.5, 0.2)),
            Node("Flame_Sphere", key=flame_key, prim="sphere", material="M_Torch_On", pos=(0, 1.15, 0), scale=(0.3, 0.3, 0.3)),
            Node("Light_Point", key=light_key, light={"color": (1, 0.7, 0.35), "intensity": 1.5, "rng": 4}, pos=(0, 1.15, 0)),
        ],
    )


def door_node(key_prefix="door", name="Door", pos=(0, 0, 0)):
    panel_key = key_prefix + ".panel"

    def door_fields(reg):
        return (
            "  doorPanel: %s\n" % ref(reg[panel_key].t) +
            "  startOpen: 0\n"
        )

    return Node(
        name, key=key_prefix, pos=pos,
        monos=[{"script": "DemoDoor", "fields": door_fields}],
        children=[
            Node("Frame_Left", prim="cube", material="M_Door", pos=(-1.25, 1.5, 0), scale=(0.5, 3, 0.5)),
            Node("Frame_Right", prim="cube", material="M_Door", pos=(1.25, 1.5, 0), scale=(0.5, 3, 0.5)),
            Node("DoorPanel", key=panel_key, prim="cube", material="M_Wood", pos=(0, 1.25, 0), scale=(2, 2.5, 0.2)),
        ],
    )


def dummy_node(key_prefix="dummy", name="DummyTarget", pos=(0, 0, 0)):
    return Node(
        name, key=key_prefix, pos=pos,
        monos=[{"script": "DemoDummyTarget", "fields": "  IsImmortal: 1\n"}],
        children=[
            Node("Body_Capsule", prim="capsule", material="M_Dummy", pos=(0, 1, 0), scale=(0.6, 0.8, 0.6)),
            Node("Head_Sphere", prim="sphere", material="M_Dummy", pos=(0, 2.1, 0), scale=(0.5, 0.5, 0.5)),
            Node("Hitbox", box={"size": (1, 2.4, 1), "center": (0, 0, 0), "trigger": 1}, pos=(0, 1.2, 0)),
        ],
    )


def room_node(name, pos=(0, 0, 0)):
    return Node(
        name, key=name, pos=pos,
        children=[Node("Floor_Cube", prim="cube", material="M_Stone", pos=(0, -0.05, 0), scale=(8, 0.1, 8))],
    )


def player_spawn_node(name="PlayerSpawn", pos=(0, 0, 0)):
    return Node(name, key="spawn", pos=pos)


# --------------------------------------------------------------------------- file builders

def build_prefab(root, start=600000):
    alloc = Allocator(start)
    reg = {}
    allocate(root, alloc, reg)
    docs = []
    render(root, docs, 0, reg)
    return HEADER + "".join(docs)


SCENE_DEFAULTS = """--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 00000000000000000000000000000000
  m_OcclusionCullingData: {fileID: 0}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 9
  m_Fog: 0
  m_FogColor: {r: 0.5, g: 0.5, b: 0.5, a: 1}
  m_FogMode: 3
  m_FogDensity: 0.01
  m_LinearFogStart: 0
  m_LinearFogEnd: 300
  m_AmbientSkyColor: {r: 0.212, g: 0.227, b: 0.259, a: 1}
  m_AmbientEquatorColor: {r: 0.114, g: 0.125, b: 0.133, a: 1}
  m_AmbientGroundColor: {r: 0.047, g: 0.043, b: 0.035, a: 1}
  m_AmbientIntensity: 1
  m_AmbientMode: 0
  m_SubtractiveShadowColor: {r: 0.42, g: 0.478, b: 0.627, a: 1}
  m_SkyboxMaterial: {fileID: 10304, guid: 0000000000000000f000000000000000, type: 0}
  m_HaloStrength: 0.5
  m_FlareStrength: 1
  m_FlareFadeSpeed: 3
  m_HaloTexture: {fileID: 0}
  m_SpotCookie: {fileID: 10001, guid: 0000000000000000e000000000000000, type: 0}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {fileID: 0}
  m_Sun: {fileID: 0}
  m_IndirectSpecularColor: {r: 0.44657898, g: 0.4964133, b: 0.5748178, a: 1}
  m_UseRadianceAmbientProbe: 0
--- !u!157 &3
LightmapSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 11
  m_GIWorkflowMode: 1
  m_GISettings:
    serializedVersion: 2
    m_BounceScale: 1
    m_IndirectOutputScale: 1
    m_AlbedoBoost: 1
    m_EnvironmentLightingMode: 0
    m_EnableBakedLightmaps: 1
    m_EnableRealtimeLightmaps: 0
  m_LightmapEditorSettings:
    serializedVersion: 12
    m_Resolution: 2
    m_BakeResolution: 40
    m_AtlasSize: 1024
    m_AO: 0
    m_AOMaxDistance: 1
    m_CompAOExponent: 1
    m_CompAOExponentDirect: 0
    m_ExtractAmbientOcclusion: 0
    m_Padding: 2
    m_LightmapParameters: {fileID: 0}
    m_LightmapsBakeMode: 1
    m_TextureCompression: 1
    m_FinalGather: 0
    m_FinalGatherFiltering: 1
    m_FinalGatherRayCount: 256
    m_ReflectionCompression: 2
    m_MixedBakeMode: 2
    m_BakeBackend: 1
    m_PVRSampling: 1
    m_PVRDirectSampleCount: 32
    m_PVRSampleCount: 512
    m_PVRBounces: 2
    m_PVREnvironmentSampleCount: 256
    m_PVREnvironmentReferencePointCount: 2048
    m_PVRFilteringMode: 1
    m_PVRDenoiserTypeDirect: 1
    m_PVRDenoiserTypeIndirect: 1
    m_PVRDenoiserTypeAO: 1
    m_PVRFilterTypeDirect: 0
    m_PVRFilterTypeIndirect: 0
    m_PVRFilterTypeAO: 0
    m_PVREnvironmentMIS: 1
    m_PVRCulling: 1
    m_PVRFilteringGaussRadiusDirect: 1
    m_PVRFilteringGaussRadiusIndirect: 5
    m_PVRFilteringGaussRadiusAO: 2
    m_PVRFilteringAtrousPositionSigmaDirect: 0.5
    m_PVRFilteringAtrousPositionSigmaIndirect: 2
    m_PVRFilteringAtrousPositionSigmaAO: 1
    m_ExportTrainingData: 0
    m_TrainingDataDestination: TrainingData
    m_LightProbeSampleCountMultiplier: 4
  m_LightingDataAsset: {fileID: 0}
  m_UseShadowmask: 1
--- !u!196 &4
NavMeshSettings:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_BuildSettings:
    serializedVersion: 2
    agentTypeID: 0
    agentRadius: 0.5
    agentHeight: 2
    agentSlope: 45
    agentClimb: 0.4
    ledgeDropHeight: 0
    maxJumpAcrossDistance: 0
    minRegionArea: 2
    manualCellSize: 0
    cellSize: 0.16666667
    manualTileSize: 0
    tileSize: 256
    accuratePlacement: 0
    debug:
      m_Flags: 0
  m_NavMeshData: {fileID: 0}
"""


def build_scene():
    alloc = Allocator(100)
    reg = {}

    roots = [
        room_node("Room_Start", pos=(0, 0, 0)),
        room_node("Room_Combat", pos=(12, 0, 0)),
        door_node("door", "Door", pos=(6, 0, 0)),
        torch_node("torch1", "Torch_01", pos=(-3, 0, -3)),
        torch_node("torch2", "Torch_02", pos=(3, 0, -3)),
        torch_node("torch3", "Torch_03", pos=(-3, 0, 3)),
        torch_node("torch4", "Torch_04", pos=(3, 0, 3)),
        dummy_node("dummy", "DummyTarget", pos=(12, 0, 0)),
        player_spawn_node("PlayerSpawn", pos=(0, 0, -2)),
    ]

    def controller_roomstate_fields(reg):
        ids = [reg["torch%d" % i].mono_ids[0] for i in (1, 2, 3, 4)]
        lines = "  torches:\n" + "".join("  - {fileID: %d}\n" % i for i in ids)
        return lines

    # Forward references: roomState mono is index 0, bootstrap mono is index 1 on the same GO.
    controller = Node(
        "RoomStateController", key="controller", pos=(0, 0, 0),
        monos=[
            {"script": "DemoRoomState", "fields": controller_roomstate_fields},
            {"script": "DemoBootstrap", "fields": None},  # filled after allocation below
        ],
    )
    roots.append(controller)

    for r in roots:
        allocate(r, alloc, reg)

    def bootstrap_fields(reg):
        return (
            "  roomState: %s\n" % ref(reg["controller"].mono_ids[0]) +
            "  door: %s\n" % ref(reg["door"].mono_ids[0])
        )

    controller.monos[1]["fields"] = bootstrap_fields

    docs = []
    for r in roots:
        render(r, docs, 0, reg)

    return HEADER + SCENE_DEFAULTS + "".join(docs)


# --------------------------------------------------------------------------- .meta builders

def meta_common_tail():
    return ("  userData: \n"
            "  assetBundleName: \n"
            "  assetBundleVariant: \n")


def meta_folder(g):
    return ("fileFormatVersion: 2\n"
            "guid: %s\n" % g +
            "folderAsset: yes\n"
            "DefaultImporter:\n"
            "  externalObjects: {}\n"
            + meta_common_tail())


def meta_script(g):
    return ("fileFormatVersion: 2\n"
            "guid: %s\n" % g +
            "MonoImporter:\n"
            "  externalObjects: {}\n"
            "  serializedVersion: 2\n"
            "  defaultReferences: []\n"
            "  executionOrder: 0\n"
            "  icon: {instanceID: 0}\n"
            + meta_common_tail())


def meta_asmdef(g):
    return ("fileFormatVersion: 2\n"
            "guid: %s\n" % g +
            "AssemblyDefinitionImporter:\n"
            "  externalObjects: {}\n"
            + meta_common_tail())


def meta_material(g):
    return ("fileFormatVersion: 2\n"
            "guid: %s\n" % g +
            "NativeFormatImporter:\n"
            "  externalObjects: {}\n"
            "  mainObjectFileID: %d\n" % MAT_MAIN_ID +
            meta_common_tail())


def meta_prefab(g):
    return ("fileFormatVersion: 2\n"
            "guid: %s\n" % g +
            "PrefabImporter:\n"
            "  externalObjects: {}\n"
            + meta_common_tail())


def meta_scene(g):
    return ("fileFormatVersion: 2\n"
            "guid: %s\n" % g +
            "DefaultImporter:\n"
            "  externalObjects: {}\n"
            + meta_common_tail())


def meta_text(g):
    return ("fileFormatVersion: 2\n"
            "guid: %s\n" % g +
            "TextScriptImporter:\n"
            "  externalObjects: {}\n"
            + meta_common_tail())


# --------------------------------------------------------------------------- writing

def write(rel_path, content):
    full = os.path.join(PROJECT_ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", newline="\n") as f:
        f.write(content)
    return rel_path


def main():
    written = []

    # Folder metas
    folders = ["Assets/Demo", "Assets/Demo/Scenes", "Assets/Demo/Prefabs", "Assets/Demo/Materials",
               "Assets/Demo/Scripts", "Assets/Demo/Editor", "Assets/Demo/Tests",
               "Assets/Demo/Tests/EditMode", "Assets/Demo/Tests/PlayMode"]
    for f in folders:
        written.append(write(f + ".meta", meta_folder(G[f])))

    # Script + asmdef metas (source files are authored separately)
    scripts = ["Assets/Demo/Scripts/DemoTorch.cs", "Assets/Demo/Scripts/DemoDoor.cs",
               "Assets/Demo/Scripts/DemoRoomState.cs", "Assets/Demo/Scripts/DemoDummyTarget.cs",
               "Assets/Demo/Scripts/DemoBootstrap.cs", "Assets/Demo/Editor/DemoAssetGenerator.cs",
               "Assets/Demo/Tests/EditMode/DemoAssetIntegrityTests.cs",
               "Assets/Demo/Tests/PlayMode/MiniDungeonPlayModeTests.cs"]
    for s in scripts:
        written.append(write(s + ".meta", meta_script(G[s])))

    asmdefs = ["Assets/Demo/Scripts/DemoDungeon.Runtime.asmdef",
               "Assets/Demo/Editor/DemoDungeon.Editor.asmdef",
               "Assets/Demo/Tests/EditMode/DemoDungeon.EditMode.Tests.asmdef",
               "Assets/Demo/Tests/PlayMode/DemoDungeon.PlayMode.Tests.asmdef"]
    for a in asmdefs:
        written.append(write(a + ".meta", meta_asmdef(G[a])))

    # Materials
    for name, (color, smooth) in MATERIALS.items():
        rel = "Assets/Demo/Materials/%s.mat" % name
        written.append(write(rel, material_doc(name, color, smooth)))
        written.append(write(rel + ".meta", meta_material(G[rel])))

    # Prefabs
    prefab_roots = {
        "Room_Start": room_node("Room_Start"),
        "Room_Combat": room_node("Room_Combat"),
        "Door": door_node(),
        "Torch": torch_node("torch", "Torch"),
        "DummyTarget": dummy_node(),
        "PlayerSpawn": player_spawn_node(),
    }
    for name, root in prefab_roots.items():
        rel = "Assets/Demo/Prefabs/%s.prefab" % name
        written.append(write(rel, build_prefab(root)))
        written.append(write(rel + ".meta", meta_prefab(G[rel])))

    # Scene
    rel = "Assets/Demo/Scenes/MiniDungeon.unity"
    written.append(write(rel, build_scene()))
    written.append(write(rel + ".meta", meta_scene(G[rel])))

    # README.md meta (content authored separately)
    written.append(write("Assets/Demo/README.md.meta", meta_text(G["Assets/Demo/README.md"])))

    print("Generated %d files:" % len(written))
    for w in sorted(written):
        print("  " + w)


if __name__ == "__main__":
    main()
