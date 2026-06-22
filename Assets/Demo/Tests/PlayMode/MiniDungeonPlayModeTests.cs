using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
#if UNITY_EDITOR
using UnityEditor.SceneManagement;
#endif

namespace DemoDungeon.Tests
{
    /// <summary>
    /// PlayMode tests for the MiniDungeon demo fixture. These enter play mode, load the demo
    /// scene, and verify runtime behavior of the demo components.
    /// </summary>
    public class MiniDungeonPlayModeTests
    {
        private const string ScenePath = "Assets/Demo/Scenes/MiniDungeon.unity";

        [UnitySetUp]
        public IEnumerator LoadDemoScene()
        {
#if UNITY_EDITOR
            // Load the scene by path in play mode without requiring it to be in Build Settings.
            EditorSceneManager.LoadSceneInPlayMode(
                ScenePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            SceneManager.LoadScene("MiniDungeon");
#endif
            // Allow the scene to activate and Awake/Start to run.
            yield return null;
            yield return null;
        }

        [UnityTest]
        public IEnumerator DemoScene_LoadsWithFourTorches()
        {
            DemoTorch[] torches = Object.FindObjectsByType<DemoTorch>(FindObjectsSortMode.None);
            Assert.AreEqual(4, torches.Length, "Loaded scene must contain exactly four torches.");
            yield break;
        }

        [UnityTest]
        public IEnumerator DummyTarget_IsImmortal_AndSurvivesManyHits()
        {
            DemoDummyTarget dummy = Object.FindFirstObjectByType<DemoDummyTarget>();
            Assert.IsNotNull(dummy, "Combat room must contain a dummy target.");
            Assert.IsTrue(dummy.IsImmortal, "Dummy target must be immortal.");

            const int hits = 50;
            for (int i = 0; i < hits; i++)
            {
                dummy.RegisterHit();
            }
            yield return null;

            Assert.IsNotNull(dummy, "Immortal dummy must never be destroyed by hits.");
            Assert.IsTrue(dummy.gameObject.activeInHierarchy, "Immortal dummy must remain active.");
            Assert.AreEqual(hits, dummy.HitCount, "Every hit should be counted.");
        }

        [UnityTest]
        public IEnumerator StartRoom_CompletesWhenAllTorchesLit()
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
            yield return null;

            Assert.IsTrue(roomState.IsStartRoomComplete, "Room should be complete once all torches are lit.");
        }

        [UnityTest]
        public IEnumerator Door_OpensAndCloses()
        {
            DemoDoor door = Object.FindFirstObjectByType<DemoDoor>();
            Assert.IsNotNull(door, "Scene must contain a door.");

            door.Open();
            Assert.IsTrue(door.IsOpen, "Door should report open after Open().");

            door.Close();
            Assert.IsFalse(door.IsOpen, "Door should report closed after Close().");
            yield break;
        }
    }
}
