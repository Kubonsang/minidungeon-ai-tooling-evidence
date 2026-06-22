using UnityEngine;

namespace DemoDungeon
{
    /// <summary>
    /// A torch whose lit state drives an optional point Light and a flame material swap.
    /// Part of the copyright-safe MiniDungeon demo fixture (no external assets, no extra packages).
    /// </summary>
    [DisallowMultipleComponent]
    public class DemoTorch : MonoBehaviour
    {
        [Tooltip("Initial lit state applied on Awake.")]
        [SerializeField] private bool startLit;

        [Tooltip("Optional point light toggled with the lit state.")]
        [SerializeField] private Light pointLight;

        [Tooltip("Optional flame renderer whose material is swapped with the lit state.")]
        [SerializeField] private MeshRenderer flameRenderer;

        [SerializeField] private Material litMaterial;
        [SerializeField] private Material unlitMaterial;

        /// <summary>True when the torch is currently lit.</summary>
        public bool IsLit { get; private set; }

        private void Awake()
        {
            ApplyState(startLit);
        }

        /// <summary>Set the lit state and update the light / material accordingly.</summary>
        public void SetLit(bool value)
        {
            ApplyState(value);
        }

        /// <summary>Flip the current lit state.</summary>
        public void Toggle()
        {
            ApplyState(!IsLit);
        }

        private void ApplyState(bool value)
        {
            IsLit = value;

            if (pointLight != null)
            {
                pointLight.enabled = value;
            }

            if (flameRenderer != null)
            {
                Material target = value ? litMaterial : unlitMaterial;
                if (target != null)
                {
                    flameRenderer.sharedMaterial = target;
                }
            }
        }
    }
}
