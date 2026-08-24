Refresh menu state fix

Replace:
- KeyboardOverlayApp.swift
- BLETransport.swift

What changed:
- Removes the temporary RAW/DECODED diagnostic logging by returning to the
  clean refresh-fixed BLETransport.
- The menu item now observes BLETransport.isRefreshingKeymap.
- During a refresh it becomes:
      Refreshing Keymap…
  and is disabled.
- When the transaction finishes it automatically returns to:
      Refresh Keymap
- A second invocation while refreshing is silently ignored.

Why you saw the message:
- On the first refresh after behavior-cache migration, the overlay could become
  visually correct before all behavior metadata finished loading.
- isRefreshingKeymap intentionally stayed true until:
      Manual keymap refresh complete
- The newly persisted behavior metadata means later refreshes should usually
  skip that long first-run behavior loading sequence.
