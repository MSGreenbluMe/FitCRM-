# Lessons Learned

## 2025-12-19

- ESM-based static demos should be served over HTTP (not `file://`) to avoid module loading restrictions.
- Stitch/Tailwind mockups can be turned into a working prototype quickly by:
  - defining a minimal in-memory state model
  - adding hash-based routing
  - persisting state to `localStorage`
