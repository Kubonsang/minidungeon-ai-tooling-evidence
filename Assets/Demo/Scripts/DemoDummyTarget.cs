using UnityEngine;

namespace DemoDungeon
{
    /// <summary>
    /// An immortal practice dummy. Counts hits but is never destroyed or disabled by them.
    /// Part of the copyright-safe MiniDungeon demo fixture.
    /// </summary>
    [DisallowMultipleComponent]
    public class DemoDummyTarget : MonoBehaviour
    {
        [Tooltip("When true the dummy can never be destroyed by hits. Always true for this fixture.")]
        public bool IsImmortal = true;

        /// <summary>Number of hits registered since the last reset.</summary>
        public int HitCount { get; private set; }

        /// <summary>
        /// Register a hit. The dummy is immortal, so this only increments the counter
        /// and never destroys or disables the GameObject.
        /// </summary>
        public void RegisterHit()
        {
            HitCount++;
        }

        /// <summary>Reset the hit counter.</summary>
        public void ResetHits()
        {
            HitCount = 0;
        }
    }
}
