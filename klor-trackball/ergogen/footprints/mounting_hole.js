module.exports = {
  params: {
    designator: 'MH',
    drill: 3.2
  },
  body: p => `
    (module KLOR_MOUNTING_HOLE (layer F.Cu)
      ${p.at}
      (fp_text reference "${p.ref}" (at 0 0) (layer F.SilkS) hide
        (effects (font (size 1 1) (thickness 0.15))))
      (pad "" np_thru_hole circle (at 0 0) (size ${p.drill} ${p.drill}) (drill ${p.drill}) (layers *.Cu *.Mask))
    )
  `
}
