// One-sided Alps SKRTLAE010 reset footprint derived from stock KLOR.
module.exports = {
  params: {
    designator: 'RST',
    side: 'F',
    reset: undefined,
    gnd: {type:'net',value:'GND'}
  },
  body: p => {
    const side=p.side==='B'?'B':'F'
    const mirror=side==='B'?' (justify mirror)':''
    return `
      (module KLOR_SKRTLAE010_RESET (layer ${side}.Cu)
        ${p.at}
        (fp_text reference "${p.ref}" (at 0 -2.7) (layer ${side}.SilkS) ${p.ref_hide}
          (effects (font (size 1 1) (thickness 0.15))${mirror}))
        (fp_rect (start -2.25 -1.35) (end 2.25 1.21) (layer ${side}.Fab) (width 0.1) (fill none))
        (pad 1 smd roundrect (at -1.225 -0.9 ${p.r}) (size 0.75 1.8) (layers ${side}.Cu ${side}.Paste ${side}.Mask) (roundrect_rratio 0.25) ${p.reset})
        (pad 1 smd roundrect (at 1.225 -0.9 ${p.r}) (size 0.75 1.8) (layers ${side}.Cu ${side}.Paste ${side}.Mask) (roundrect_rratio 0.25) ${p.reset})
        (pad 2 smd roundrect (at 0 -0.9 ${p.r}) (size 0.6 1.8) (layers ${side}.Cu ${side}.Paste ${side}.Mask) (roundrect_rratio 0.25) ${p.gnd})
        (pad MP smd roundrect (at -1.85 1.05 ${p.r}) (size 1.3 0.9) (layers ${side}.Cu ${side}.Paste ${side}.Mask) (roundrect_rratio 0.25))
        (pad MP smd roundrect (at 1.85 1.05 ${p.r}) (size 1.3 0.9) (layers ${side}.Cu ${side}.Paste ${side}.Mask) (roundrect_rratio 0.25))
      )
    `
  }
}
