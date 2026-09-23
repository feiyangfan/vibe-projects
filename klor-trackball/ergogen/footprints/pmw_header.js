// Frozen Task-2D keyboard-side Kivipallur mating header.
module.exports = {
  params: {
    designator: 'J',
    P1: undefined, P2: undefined, P3: undefined, P4: undefined,
    P5: undefined, P6: undefined, P7: undefined
  },
  body: p => {
    const nets=[p.P1,p.P2,p.P3,p.P4,p.P5,p.P6,p.P7]
    return `
      (module KLOR_PMW_1X07_P2_54 (layer F.Cu)
        ${p.at}
        (fp_text reference "${p.ref}" (at 2.2 0 90) (layer F.SilkS) ${p.ref_hide}
          (effects (font (size 1 1) (thickness 0.15))))
        (fp_rect (start -1.27 -8.89) (end 1.27 8.89) (layer F.SilkS) (width 0.12) (fill none))
        ${nets.map((net,i)=>`(pad ${i+1} thru_hole ${i===0?'rect':'circle'} (at 0 ${-7.62+i*2.54} ${p.r}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) ${net || ''})`).join('\n')}
      )
    `
  }
}
