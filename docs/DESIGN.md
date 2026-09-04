# Design principles

## Pure specifications, narrow Unreal adapters

Preset lookup, validation, camera math, and registries run on ordinary Python.
Actor construction imports Unreal lazily at the call boundary. This keeps CI
meaningful without creating a fake claim that CI rendered a level.

## Read back every reflected property

`set_editor_property` returning is not enough. The library records the value
before the write, the requested value, and the value read afterward. Missing,
inert, and nonconforming results have different exception types.

## Structs require a write-back

Unreal can expose reflected structs as value-like wrappers. Updating a field
on the local wrapper may not update its owner. Camera focus therefore mutates
the struct, assigns it to the component, then reads the committed fields from
the component again.

## Persistent VFX means an actor in the level

Runtime Niagara spawn helpers can create transient components. An MRQ child
process loading the saved level cannot see editor-only transient state. Scene
Kit uses `NiagaraActor` and assigns its component asset so the actor can be
serialized when the caller saves the level.

## Lifecycle is caller-owned

The library does not create, clear, save, or render a map as a side effect of
building a scene foundation. `save_current_level(confirmed=True)` exists as a
separate operation so destructive boundaries remain visible in the script.

