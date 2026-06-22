using UnityEngine;

namespace DemoDungeon
{
    /// <summary>
    /// A simple door between the two rooms. Open/Close slides an optional panel transform.
    /// Part of the copyright-safe MiniDungeon demo fixture.
    /// </summary>
    [DisallowMultipleComponent]
    public class DemoDoor : MonoBehaviour
    {
        // Local Y offset applied to the panel when the door is open.
        private const float OpenHeight = 2.5f;

        [Tooltip("Optional panel transform that slides up when the door opens.")]
        [SerializeField] private Transform doorPanel;

        [Tooltip("Initial open state applied on Awake.")]
        [SerializeField] private bool startOpen;

        /// <summary>True when the door is currently open.</summary>
        public bool IsOpen { get; private set; }

        private void Awake()
        {
            if (startOpen)
            {
                Open();
            }
            else
            {
                Close();
            }
        }

        /// <summary>Open the door.</summary>
        public void Open()
        {
            IsOpen = true;
            if (doorPanel != null)
            {
                doorPanel.localPosition = new Vector3(0f, OpenHeight, 0f);
            }
        }

        /// <summary>Close the door.</summary>
        public void Close()
        {
            IsOpen = false;
            if (doorPanel != null)
            {
                doorPanel.localPosition = Vector3.zero;
            }
        }

        /// <summary>Flip the current open state.</summary>
        public void Toggle()
        {
            if (IsOpen)
            {
                Close();
            }
            else
            {
                Open();
            }
        }
    }
}
