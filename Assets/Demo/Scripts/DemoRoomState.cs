using UnityEngine;

namespace DemoDungeon
{
    /// <summary>
    /// Tracks completion of the start room: the room is "complete" once all four torches are lit.
    /// References torches via the inspector, or discovers them at runtime as a fallback.
    /// Part of the copyright-safe MiniDungeon demo fixture.
    /// </summary>
    [DisallowMultipleComponent]
    public class DemoRoomState : MonoBehaviour
    {
        [Tooltip("The torches that must all be lit for the start room to be complete.")]
        [SerializeField] private DemoTorch[] torches = new DemoTorch[0];

        /// <summary>Number of torches currently tracked.</summary>
        public int TorchCount => GetTorches().Length;

        /// <summary>True when at least one torch is tracked and every tracked torch is lit.</summary>
        public bool IsStartRoomComplete
        {
            get
            {
                DemoTorch[] tracked = GetTorches();
                if (tracked.Length == 0)
                {
                    return false;
                }

                for (int i = 0; i < tracked.Length; i++)
                {
                    if (tracked[i] == null || !tracked[i].IsLit)
                    {
                        return false;
                    }
                }

                return true;
            }
        }

        /// <summary>Explicitly assign the tracked torches (used by the bootstrap / tests).</summary>
        public void SetTorches(DemoTorch[] value)
        {
            torches = value ?? new DemoTorch[0];
        }

        private DemoTorch[] GetTorches()
        {
            if (torches != null && torches.Length > 0)
            {
                return torches;
            }

            // Fallback discovery keeps the fixture robust even if references are not wired.
            torches = FindObjectsByType<DemoTorch>(FindObjectsSortMode.InstanceID);
            return torches;
        }
    }
}
