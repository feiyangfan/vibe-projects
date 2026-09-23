// MJ-4PP-9 TRRS, one mounting side at a time, source-derived from stock KLOR.
module.exports = {
  params: {
    designator: 'J',
    side: 'F',
    P1: undefined, P2: undefined, P3: undefined, P4: undefined
  },
  body: p => {
    const F = p.side === 'F'
    const stabX = F ? 0 : -1.75
    const pos = F
      ? {1:[2.1,10.3],2:[2.1,6.3],3:[-2.1,11.8],4:[2.1,3.3]}
      : {1:[-3.85,10.3],2:[-3.85,6.3],3:[0.35,11.8],4:[-3.85,3.3]}
    const nets={1:p.P1,2:p.P2,3:p.P3,4:p.P4}
    const side=F?'F':'B'
    return `
      (module KLOR_MJ_4PP_9 (layer F.Cu)
        ${p.at}
        (fp_text reference "${p.ref}" (at -0.8 6.4) (layer ${side}.SilkS) ${p.ref_hide}
          (effects (font (size 1 1) (thickness 0.15))${F?'':' (justify mirror)'}))
        (fp_rect (start -3 0) (end 3 12) (layer ${side}.SilkS) (width 0.15) (fill none))
        (pad "" np_thru_hole circle (at ${stabX} 1.5) (size 1.2 1.2) (drill 1.2) (layers *.Cu *.Mask))
        (pad "" np_thru_hole circle (at ${stabX} 8.5) (size 1.2 1.2) (drill 1.2) (layers *.Cu *.Mask))
        ${[1,2,3,4].map(n=>`(pad ${n} thru_hole oval (at ${pos[n][0]} ${pos[n][1]} ${p.r}) (size 1.7 2.5) (drill oval 1 1.5) (layers *.Cu *.Mask) ${nets[n]})`).join('\n')}
      )
    `
  }
}
