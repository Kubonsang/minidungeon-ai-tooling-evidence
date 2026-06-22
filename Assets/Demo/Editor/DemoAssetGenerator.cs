#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DemoDungeon.EditorTools
{
    /// <summary>
    /// Deterministic, idempotent generator for the copyright-safe MiniDungeon demo fixture.
    /// Recreates all materials, prefabs, and the scene from Unity built-in primitives only.
    /// No external assets, textures, models, audio, fonts, or packages are used.
    ///
    /// Menu: Tools/Demo/Regenerate MiniDungeon Demo
    /// </summary>
    public static class DemoAssetGenerator
    {
        private const string DemoRoot = "Assets/Demo";
        private const string MaterialsDir = DemoRoot + "/Materials";
        private const string PrefabsDir = DemoRoot + "/Prefabs";
        private const string ScenesDir = DemoRoot + "/Scenes";
        private const string ScenePath = ScenesDir + "/MiniDungeon.unity";

        private const string TorchPrefab = PrefabsDir + "/Torch.prefab";
        private const string DoorPrefab = PrefabsDir + "/Door.prefab";
        private const string DummyPrefab = PrefabsDir + "/DummyTarget.prefab";
        private const string RoomStartPrefab = PrefabsDir + "/Room_Start.prefab";
        private const string RoomCombatPrefab = PrefabsDir + "/Room_Combat.prefab";
        private const string PlayerSpawnPrefab = PrefabsDir + "/PlayerSpawn.prefab";

        [MenuItem("Tools/Demo/Regenerate MiniDungeon Demo")]
        public static void Regenerate()
        {
            EnsureFolders();

            Materials materials = CreateMaterials();
            CreatePrefabs(materials);
            CreateScene();

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[DemoAssetGenerator] MiniDungeon demo regenerated (materials, prefabs, scene).");
        }

        // ------------------------------------------------------------------ folders

        private static void EnsureFolders()
        {
            EnsureFolder("Assets", "Demo");
            EnsureFolder(DemoRoot, "Materials");
            EnsureFolder(DemoRoot, "Prefabs");
            EnsureFolder(DemoRoot, "Scenes");
        }

        private static void EnsureFolder(string parent, string child)
        {
            string path = parent + "/" + child;
            if (!AssetDatabase.IsValidFolder(path))
            {
                AssetDatabase.CreateFolder(parent, child);
            }
        }

        // ------------------------------------------------------------------ materials

        private struct Materials
        {
            public Material Stone;
            public Material Wood;
            public Material TorchOn;
            public Material TorchOff;
            public Material Dummy;
            public Material Door;
        }

        private static Materials CreateMaterials()
        {
            return new Materials
            {
                Stone = CreateMaterial("M_Stone", new Color(0.5f, 0.5f, 0.5f), 0.1f),
                Wood = CreateMaterial("M_Wood", new Color(0.40f, 0.26f, 0.13f), 0.1f),
                TorchOn = CreateMaterial("M_Torch_On", new Color(1.0f, 0.55f, 0.15f), 0.3f),
                TorchOff = CreateMaterial("M_Torch_Off", new Color(0.20f, 0.16f, 0.12f), 0.1f),
                Dummy = CreateMaterial("M_Dummy", new Color(0.70f, 0.22f, 0.22f), 0.2f),
                Door = CreateMaterial("M_Door", new Color(0.30f, 0.20f, 0.12f), 0.1f),
            };
        }

        private static Material CreateMaterial(string name, Color baseColor, float smoothness)
        {
            string path = MaterialsDir + "/" + name + ".mat";

            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }

            Material mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null)
            {
                mat = new Material(shader) { name = name };
                AssetDatabase.CreateAsset(mat, path);
            }
            else
            {
                mat.shader = shader;
            }

            if (mat.HasProperty("_BaseColor"))
            {
                mat.SetColor("_BaseColor", baseColor);
            }
            if (mat.HasProperty("_Color"))
            {
                mat.SetColor("_Color", baseColor);
            }
            if (mat.HasProperty("_Smoothness"))
            {
                mat.SetFloat("_Smoothness", smoothness);
            }
            if (mat.HasProperty("_Metallic"))
            {
                mat.SetFloat("_Metallic", 0f);
            }

            EditorUtility.SetDirty(mat);
            return mat;
        }

        // ------------------------------------------------------------------ prefabs

        private static void CreatePrefabs(Materials m)
        {
            BuildTorch(m);
            BuildDoor(m);
            BuildDummyTarget(m);
            BuildRoom(RoomStartPrefab, "Room_Start", m.Stone);
            BuildRoom(RoomCombatPrefab, "Room_Combat", m.Stone);
            BuildPlayerSpawn();
        }

        private static void BuildTorch(Materials m)
        {
            var root = new GameObject("Torch");
            DemoTorch torch = root.AddComponent<DemoTorch>();

            NewPrimitive("Base_Cylinder", PrimitiveType.Cylinder, m.Wood, root.transform,
                new Vector3(0f, 0.5f, 0f), new Vector3(0.2f, 0.5f, 0.2f));

            GameObject flame = NewPrimitive("Flame_Sphere", PrimitiveType.Sphere, m.TorchOn, root.transform,
                new Vector3(0f, 1.15f, 0f), new Vector3(0.3f, 0.3f, 0.3f));

            var lightGo = new GameObject("Light_Point");
            lightGo.transform.SetParent(root.transform, false);
            lightGo.transform.localPosition = new Vector3(0f, 1.15f, 0f);
            Light light = lightGo.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = 4f;
            light.intensity = 1.5f;
            light.color = new Color(1.0f, 0.7f, 0.35f);

            var so = new SerializedObject(torch);
            so.FindProperty("startLit").boolValue = false;
            so.FindProperty("pointLight").objectReferenceValue = light;
            so.FindProperty("flameRenderer").objectReferenceValue = flame.GetComponent<MeshRenderer>();
            so.FindProperty("litMaterial").objectReferenceValue = m.TorchOn;
            so.FindProperty("unlitMaterial").objectReferenceValue = m.TorchOff;
            so.ApplyModifiedPropertiesWithoutUndo();

            SaveAndDestroy(root, TorchPrefab);
        }

        private static void BuildDoor(Materials m)
        {
            var root = new GameObject("Door");
            DemoDoor door = root.AddComponent<DemoDoor>();

            NewPrimitive("Frame_Left", PrimitiveType.Cube, m.Door, root.transform,
                new Vector3(-1.25f, 1.5f, 0f), new Vector3(0.5f, 3f, 0.5f));
            NewPrimitive("Frame_Right", PrimitiveType.Cube, m.Door, root.transform,
                new Vector3(1.25f, 1.5f, 0f), new Vector3(0.5f, 3f, 0.5f));
            GameObject panel = NewPrimitive("DoorPanel", PrimitiveType.Cube, m.Wood, root.transform,
                new Vector3(0f, 1.25f, 0f), new Vector3(2f, 2.5f, 0.2f));

            var so = new SerializedObject(door);
            so.FindProperty("startOpen").boolValue = false;
            so.FindProperty("doorPanel").objectReferenceValue = panel.transform;
            so.ApplyModifiedPropertiesWithoutUndo();

            SaveAndDestroy(root, DoorPrefab);
        }

        private static void BuildDummyTarget(Materials m)
        {
            var root = new GameObject("DummyTarget");
            DemoDummyTarget dummy = root.AddComponent<DemoDummyTarget>();
            dummy.IsImmortal = true;

            NewPrimitive("Body_Capsule", PrimitiveType.Capsule, m.Dummy, root.transform,
                new Vector3(0f, 1f, 0f), new Vector3(0.6f, 0.8f, 0.6f));
            NewPrimitive("Head_Sphere", PrimitiveType.Sphere, m.Dummy, root.transform,
                new Vector3(0f, 2.1f, 0f), new Vector3(0.5f, 0.5f, 0.5f));

            var hitbox = new GameObject("Hitbox");
            hitbox.transform.SetParent(root.transform, false);
            hitbox.transform.localPosition = new Vector3(0f, 1.2f, 0f);
            BoxCollider box = hitbox.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.size = new Vector3(1f, 2.4f, 1f);

            SaveAndDestroy(root, DummyPrefab);
        }

        private static void BuildRoom(string prefabPath, string rootName, Material floorMat)
        {
            var root = new GameObject(rootName);
            NewPrimitive("Floor_Cube", PrimitiveType.Cube, floorMat, root.transform,
                new Vector3(0f, -0.05f, 0f), new Vector3(8f, 0.1f, 8f));
            SaveAndDestroy(root, prefabPath);
        }

        private static void BuildPlayerSpawn()
        {
            // Pure marker: a single empty GameObject (Transform only).
            var root = new GameObject("PlayerSpawn");
            SaveAndDestroy(root, PlayerSpawnPrefab);
        }

        // ------------------------------------------------------------------ scene

        private static void CreateScene()
        {
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            InstantiateAt(RoomStartPrefab, new Vector3(0f, 0f, 0f));
            InstantiateAt(RoomCombatPrefab, new Vector3(12f, 0f, 0f));
            GameObject doorGo = InstantiateAt(DoorPrefab, new Vector3(6f, 0f, 0f));

            // Four torches in the start room corners.
            var torches = new DemoTorch[4];
            Vector3[] corners =
            {
                new Vector3(-3f, 0f, -3f),
                new Vector3(3f, 0f, -3f),
                new Vector3(-3f, 0f, 3f),
                new Vector3(3f, 0f, 3f),
            };
            for (int i = 0; i < corners.Length; i++)
            {
                GameObject t = InstantiateAt(TorchPrefab, corners[i]);
                t.name = "Torch_0" + (i + 1);
                torches[i] = t.GetComponent<DemoTorch>();
            }

            GameObject dummyGo = InstantiateAt(DummyPrefab, new Vector3(12f, 0f, 0f));
            dummyGo.name = "DummyTarget";

            InstantiateAt(PlayerSpawnPrefab, new Vector3(0f, 0f, -2f));

            // Single room-state / goal controller object.
            var controller = new GameObject("RoomStateController");
            DemoRoomState roomState = controller.AddComponent<DemoRoomState>();
            DemoBootstrap bootstrap = controller.AddComponent<DemoBootstrap>();
            roomState.SetTorches(torches);

            var so = new SerializedObject(bootstrap);
            so.FindProperty("roomState").objectReferenceValue = roomState;
            so.FindProperty("door").objectReferenceValue = doorGo.GetComponent<DemoDoor>();
            so.ApplyModifiedPropertiesWithoutUndo();

            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene, ScenePath);
        }

        private static GameObject InstantiateAt(string prefabPath, Vector3 position)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            instance.transform.position = position;
            return instance;
        }

        // ------------------------------------------------------------------ helpers

        private static GameObject NewPrimitive(string name, PrimitiveType type, Material mat, Transform parent,
            Vector3 localPosition, Vector3 localScale)
        {
            GameObject go = GameObject.CreatePrimitive(type);
            go.name = name;

            Collider col = go.GetComponent<Collider>();
            if (col != null)
            {
                Object.DestroyImmediate(col);
            }

            go.GetComponent<MeshRenderer>().sharedMaterial = mat;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPosition;
            go.transform.localScale = localScale;
            return go;
        }

        private static void SaveAndDestroy(GameObject go, string prefabPath)
        {
            PrefabUtility.SaveAsPrefabAsset(go, prefabPath);
            Object.DestroyImmediate(go);
        }
    }
}
#endif
