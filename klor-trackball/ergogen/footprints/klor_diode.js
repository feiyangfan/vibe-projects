// Single-side SOD-123 footprint derived from the stock KLOR pad geometry.
// The stock reversible footprint used plated micro-holes to duplicate the SMD
// lands on both sides; Rev 1 uses ordinary SMD lands on the selected side.
module.exports = {
  params: {
    designator: 'D',
    side: 'B',
    row: undefined,
    sw: undefined
  },
  body: p => {
    const side = p.side === 'F' ? 'F' : 'B'
    const mirror = side === 'B' ? ' (justify mirror)' : ''
    return `
      (module KLOR_D_SOD123 (layer ${side}.Cu)
        ${p.at}
        (fp_text reference "${p.ref}" (at 0 1.5) (layer ${side}.SilkS) ${p.ref_hide}
          (effects (font (size 1 1) (thickness 0.15))${mirror}))
        (fp_text value "1N4148W_SOD-123" (at 0 -1.5) (layer ${side}.Fab) hide
          (effects (font (size 1 1) (thickness 0.15))${mirror}))
        (fp_line (start -0.5 -0.7) (end -0.5 0.7) (layer ${side}.SilkS) (width 0.15))
        (fp_line (start -0.5 0) (end 0.4 -0.7) (layer ${side}.SilkS) (width 0.15))
        (fp_line (start 0.4 -0.7) (end 0.4 0.7) (layer ${side}.SilkS) (width 0.15))
        (fp_line (start 0.4 0.7) (end -0.5 0) (layer ${side}.SilkS) (width 0.15))
        (pad 1 smd rect (at -1.7 0 ${p.r}) (size 1.8 1.5) (layers ${side}.Cu ${side}.Paste ${side}.Mask) ${p.row})
        (pad 2 smd rect (at 1.7 0 ${p.r}) (size 1.8 1.5) (layers ${side}.Cu ${side}.Paste ${side}.Mask) ${p.sw})
      )
    `
  }
}
