// KLOR Rev-1 MX hotswap + SK6812MINI-E footprint.
// Geometry is source-derived from stock KLOR SK6812MINI_and_cherry,
// with reversible duplicates removed. Socket and reverse-mount LED live
// on one selected side.
module.exports = {
  params: {
    designator: 'SW',
    side: 'B',
    col: undefined,
    diode: undefined,
    dout: undefined,
    gnd: {type: 'net', value: 'GND'},
    din: undefined,
    vdd: {type: 'net', value: 'RAW_5V'}
  },
  body: p => {
    const F = p.side === 'F'
    const side = F ? 'F' : 'B'
    const socket5 = F ? [7, -2.58] : [-7, -2.58]
    const socket6 = F ? [-5.7, -5.12] : [5.7, -5.12]
    const hole5 = F ? [3.81, -2.54] : [-3.81, -2.54]
    const hole6 = F ? [-2.54, -5.08] : [2.54, -5.08]
    const led = F
      ? [[1,-2.4,6.375],[2,-2.4,4.625],[3,2.4,4.625],[4,2.4,6.375]]
      : [[1,-2.4,4.625],[2,-2.4,6.375],[3,2.4,6.375],[4,2.4,4.625]]
    const nets = {1:p.dout, 2:p.gnd, 3:p.din, 4:p.vdd}
    return `
      (module KLOR_MX_HOTSWAP_SK6812MINI_E (layer F.Cu)
        ${p.at}
        (fp_text reference "${p.ref}" (at 0 0) (layer ${side}.SilkS) ${p.ref_hide}
          (effects (font (size 1 1) (thickness 0.15))${F ? '' : ' (justify mirror)'}))
        (fp_text value "MX_HOTSWAP_SK6812MINI-E" (at 0 9) (layer ${side}.Fab) hide
          (effects (font (size 1 1) (thickness 0.15))${F ? '' : ' (justify mirror)'}))
        (fp_rect (start -7 -7) (end 7 7) (layer Dwgs.User) (width 0.15) (fill none))
        (fp_rect (start -9.525 -9.525) (end 9.525 9.525) (layer Dwgs.User) (width 0.15) (fill none))
        (fp_rect (start -1.75 3.25) (end 1.75 7.75) (layer Edge.Cuts) (width 0.12) (fill none))
        (pad "" np_thru_hole circle (at 0 0) (size 4.1 4.1) (drill 4.1) (layers *.Cu *.Mask))
        (pad "" np_thru_hole circle (at -5.08 0) (size 1.9 1.9) (drill 1.9) (layers *.Cu *.Mask))
        (pad "" np_thru_hole circle (at 5.08 0) (size 1.9 1.9) (drill 1.9) (layers *.Cu *.Mask))
        (pad "" np_thru_hole circle (at ${hole5[0]} ${hole5[1]}) (size 3 3) (drill 3) (layers *.Cu *.Mask))
        (pad "" np_thru_hole circle (at ${hole6[0]} ${hole6[1]}) (size 3 3) (drill 3) (layers *.Cu *.Mask))
        (pad 5 smd rect (at ${socket5[0]} ${socket5[1]} ${p.r}) (size 2.3 2) (layers ${side}.Cu ${side}.Paste ${side}.Mask) ${p.col})
        (pad 6 smd rect (at ${socket6[0]} ${socket6[1]} ${p.r}) (size 2.3 2) (layers ${side}.Cu ${side}.Paste ${side}.Mask) ${p.diode})
        ${led.map(([n,x,y]) => `(pad ${n} smd rect (at ${x} ${y} ${p.r}) (size 1.6 1) (layers ${side}.Cu ${side}.Paste ${side}.Mask) ${nets[n]})`).join('\n')}
      )
    `
  }
}
