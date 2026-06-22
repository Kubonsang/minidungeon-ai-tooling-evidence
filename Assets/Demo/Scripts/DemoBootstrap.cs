using UnityEngine;

namespace DemoDungeon
{
    /// <summary>
    /// Lightweight scene bootstrap. Reports initial room state and offers helper actions
    /// for tests / AI agents (light all torches, open the door). Nothing destructive.
    /// Part of the copyright-safe MiniDungeon demo fixture.
    /// </summary>
    [DisallowMultipleComponent]
    public class DemoBootstrap : MonoBehaviour
    {
        [SerializeField] private DemoRoomState roomState;
        [SerializeField] private DemoDoor door;

        private void Start()
        {
            if (roomState != null)
            {
                Debug.Log($"[DemoBootstrap] Start room complete: {roomState.IsStartRoomComplete}");
            }
        }

        /// <summary>Light every torch in the scene. Returns the number of torches lit.</summary>
        public int LightAllTorches()
        {
            DemoTorch[] torches = FindObjectsByType<DemoTorch>(FindObjectsSortMode.InstanceID);
            for (int i = 0; i < torches.Length; i++)
            {
                torches[i].SetLit(true);
            }

            return torches.Length;
        }

        /// <summary>Open the referenced door. Returns true if the door is now open.</summary>
        public bool OpenDoor()
        {
            if (door == null)
            {
                return false;
            }

            door.Open();
            return door.IsOpen;
        }
    }
}
