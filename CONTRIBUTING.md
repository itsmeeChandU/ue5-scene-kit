# Contributing

Small, evidence-backed changes are welcome.

1. Open an issue describing the Unreal version and the concrete scene problem.
2. Add or update an offline test for every pure-Python behavior.
3. For Unreal API changes, include the exact class, property, or method used.
4. Run `ruff check .`, `python -m pytest`, and `python -m build`.
5. Never commit Unreal binaries, Engine source, paid assets, project content,
   credentials, or rendered media without documented rights.

A live-engine claim should include the engine version, platform, invocation,
and an inspectable log or artifact. A test double proves our Python control
flow; it does not prove Unreal rendered the intended pixels.

