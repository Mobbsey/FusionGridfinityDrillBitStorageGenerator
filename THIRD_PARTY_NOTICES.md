# Third-party notices

## FusionGridfinityGenerator

The files in `DrillBitGridfinity/lib/gridfinityUtils/` are extracted from
[FusionGridfinityGenerator](https://github.com/Le0Michine/FusionGridfinityGenerator)
by Lev Mishin, revision
[`8a113b9fe84244d90df4d5bdb73ae0ca384a3424`](https://github.com/Le0Michine/FusionGridfinityGenerator/commit/8a113b9fe84244d90df4d5bdb73ae0ca384a3424).

The extracted files provide the Gridfinity base, solid bin body, stacking lip,
and their shared geometry utilities. The original command UI, configuration
persistence, baseplate generator, and unrelated bin modes are not included.
`DrillBitGridfinity/generators/gridfinity_generator.py` is a new adapter that
calls those geometry functions directly using this add-in's model.

The Create Drill Bit Bins toolbar icon in
`DrillBitGridfinity/commands/create_bins/resources/` is adapted from the
upstream Gridfinity bin command icon at the same pinned revision. The adapted
icon preserves the blue isometric bin motif and adds a drill bit and holder
openings to distinguish this add-in's purpose. The original 64 px reference is
retained in the resource `source/` directory.

FusionGridfinityGenerator is licensed under the Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International licence. The complete
licence text is in `LICENSE.md`. This project retains that licence, identifies
the source and revision above, and documents the extraction and adaptation.
