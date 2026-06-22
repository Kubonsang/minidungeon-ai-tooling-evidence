using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DemoDungeon.Tests
{
    /// <summary>
    /// EditMode integrity tests for the MiniDungeon demo fixture. These run without entering
    /// play mode and validate the serialized assets, references, and structural invariants.
    /// </summary>
    public class DemoAssetIntegrityTests
    {
        private const string ScenePath = "Assets/Demo/Scenes/MiniDungeon.unity";
        private const string PrefabDir = "Assets/Demo/Prefabs/";
        private const string MaterialDir = "Assets/Demo/Materials/";

        private static readonly string[] PrefabPaths =
        {
            PrefabDir + "Room_Start.prefab",
            PrefabDir + "Room_Combat.prefab",
            PrefabDir + "Door.prefab",
            PrefabDir + "Torch.prefab",
            PrefabDir + "DummyTarget.prefab",
            PrefabDir + "PlayerSpawn.prefab",
        };

        private static readonly string[] MaterialPaths =
        {
            MaterialDir + "M_Stone.mat",
            MaterialDir + "M_Wood.mat",
            MaterialDir + "M_Torch_On.mat",
            MaterialDir + "M_Torch_Off.mat",
            MaterialDir + "M_Dummy.mat",
            MaterialDir + "M_Door.mat",
        };

        private Scene _scene;

        [SetUp]
        public void SetUp()
        {
            _scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        }

        [Test]
        public void DemoScene_ExistsAndOpens()
        {
            Assert.IsTrue(File.Exists(ScenePath), "Scene file should exist on disk.");
            Assert.IsTrue(_scene.IsValid(), "Scene should open as a valid scene.");
        }

        [Test]
        public void Scene_HasExactlyFourTorches()
        {
            DemoTorch[] torches = Object.FindObjectsByType<DemoTorch>(FindObjectsSortMode.None);
            Assert.AreEqual(4, torches.Length, "The start room must contain exactly four torches.");
        }

        [Test]
        public void Scene_HasDummyTarget()
        {
            DemoDummyTarget dummy = Object.FindFirstObjectByType<DemoDummyTarget>();
            Assert.IsNotNull(dummy, "The combat room must contain a dummy target.");
        }

        [Test]
        public void DummyTarget_IsImmortal()
        {
            DemoDummyTarget dummy = Object.FindFirstObjectByType<DemoDummyTarget>();
            Assert.IsNotNull(dummy);
            Assert.IsTrue(dummy.IsImmortal, "The dummy target must be immortal.");
        }

        [Test]
        public void StartRoom_CompletesWhenAllTorchesLit()
        {
            DemoRoomState roomState = Object.FindFirstObjectByType<DemoRoomState>();
            Assert.IsNotNull(roomState, "Scene must contain a DemoRoomState controller.");

            DemoTorch[] torches = Object.FindObjectsByType<DemoTorch>(FindObjectsSortMode.None);

            foreach (DemoTorch t in torches)
            {
                t.SetLit(false);
            }
            Assert.IsFalse(roomState.IsStartRoomComplete, "Room should not be complete with torches unlit.");

            foreach (DemoTorch t in torches)
            {
                t.SetLit(true);
            }
            Assert.IsTrue(roomState.IsStartRoomComplete, "Room should be complete once all torches are lit.");
        }

        [Test]
        public void AllPrefabs_ExistAndLoad()
        {
            foreach (string path in PrefabPaths)
            {
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                Assert.IsNotNull(go, $"Required prefab missing or failed to load: {path}");
            }
        }

        [Test]
        public void Prefabs_HaveExpectedRootComponents()
        {
            AssertRootHasComponent("Torch.prefab", typeof(DemoTorch));
            AssertRootHasComponent("Door.prefab", typeof(DemoDoor));
            AssertRootHasComponent("DummyTarget.prefab", typeof(DemoDummyTarget));
        }

        [Test]
        public void Prefabs_HaveNoMissingScripts()
        {
            foreach (string path in PrefabPaths)
            {
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                Assert.IsNotNull(go, $"Prefab missing: {path}");

                MonoBehaviour[] behaviours = go.GetComponentsInChildren<MonoBehaviour>(true);
                foreach (MonoBehaviour b in behaviours)
                {
                    Assert.IsNotNull(b, $"Prefab '{path}' has a missing (null) script reference.");
                }
            }
        }

        [Test]
        public void Scene_HasNoMissingScripts()
        {
            foreach (GameObject root in _scene.GetRootGameObjects())
            {
                MonoBehaviour[] behaviours = root.GetComponentsInChildren<MonoBehaviour>(true);
                foreach (MonoBehaviour b in behaviours)
                {
                    Assert.IsNotNull(b, $"Scene object '{root.name}' has a missing (null) script reference.");
                }
            }
        }

        [Test]
        public void AllMaterials_Exist()
        {
            foreach (string path in MaterialPaths)
            {
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                Assert.IsNotNull(mat, $"Required material missing: {path}");
            }
        }

        [Test]
        public void RuntimeScripts_HaveNoExternalPackageReferences()
        {
            string[] referenced = typeof(DemoTorch).Assembly
                .GetReferencedAssemblies()
                .Select(a => a.Name)
                .ToArray();

            string[] denied =
            {
                "Unity.InputSystem",
                "Unity.RenderPipelines",
                "Unity.TextMeshPro",
                "Unity.Addressables",
                "Unity.Timeline",
                "Cinemachine",
                "Newtonsoft.Json",
            };

            foreach (string deniedName in denied)
            {
                Assert.IsFalse(
                    referenced.Any(r => r.Contains(deniedName)),
                    $"Runtime scripts must not depend on external package '{deniedName}'.");
            }

            Assert.IsTrue(
                referenced.Any(r => r.StartsWith("UnityEngine")),
                "Runtime scripts should reference UnityEngine core only.");
        }

        private static void AssertRootHasComponent(string prefabFile, System.Type componentType)
        {
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + prefabFile);
            Assert.IsNotNull(go, $"Prefab missing: {prefabFile}");
            Assert.IsNotNull(go.GetComponent(componentType),
                $"Prefab '{prefabFile}' root must have a {componentType.Name} component.");
        }
    }
}
