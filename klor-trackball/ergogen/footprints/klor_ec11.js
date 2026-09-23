// Stock KLOR EC11E geometry, retained as a through-hole production footprint.
module.exports = {
  params: {
    designator: 'ENC',
    A: undefined, B: undefined, C: undefined,
    S1: undefined, S2: undefined
  },
  body: p => `
    (module KLOR_EC11E (layer F.Cu)
      ${p.at}
      (fp_text reference "${p.ref}" (at 0 4.6) (layer F.SilkS) ${p.ref_hide}
        (effects (font (size 1 1) (thickness 0.15))))
      (fp_rect (start -6.1 -5.9) (end 6.1 5.9) (layer F.SilkS) (width 0.12) (fill none))
      (fp_circle (center 0 0) (end 3 0) (layer F.SilkS) (width 0.12) (fill none))
      (pad A thru_hole circle (at -7.5 -2.5 ${p.r}) (size 2 2) (drill 1) (layers *.Cu *.Mask) ${p.A})
      (pad B thru_hole circle (at -7.5 2.5 ${p.r}) (size 2 2) (drill 1) (layers *.Cu *.Mask) ${p.B})
      (pad C thru_hole circle (at -7.5 0 ${p.r}) (size 2 2) (drill 1) (layers *.Cu *.Mask) ${p.C})
      (pad MP thru_hole rect (at 0 -5.6 ${p.r}) (size 3.2 2) (drill oval 2.8 1.5) (layers *.Cu *.Mask))
      (pad MP thru_hole rect (at 0 5.6 ${p.r}) (size 3.2 2) (drill oval 2.8 1.5) (layers *.Cu *.Mask))
      (pad S1 thru_hole circle (at 7 2.5 ${p.r}) (size 2 2) (drill 1) (layers *.Cu *.Mask) ${p.S1})
      (pad S2 thru_hole circle (at 7 -2.5 ${p.r}) (size 2 2) (drill 1) (layers *.Cu *.Mask) ${p.S2})
    )
  `
}
