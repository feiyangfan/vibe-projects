// 0xCB Helios rev1.0 host/socket footprint.
// U1 origin and standard 12x2 hole centers match the stock KLOR ProMicro
// F-side row exactly. Helios pad 32 is added for its onboard 5V-level-shifted
// GP25 RGB output.
module.exports = {
  params: {
    designator: 'U',
    P2: undefined, P3: undefined, P4: undefined, P5: undefined,
    P6: undefined, P7: undefined, P8: undefined, P9: undefined,
    P10: undefined, P11: undefined, P12: undefined, P13: undefined,
    P19: undefined, P20: undefined, P21: undefined, P22: undefined,
    P23: undefined, P24: undefined, P25: undefined, P26: undefined,
    P27: undefined, P28: undefined, P29: undefined, P30: undefined,
    P32: undefined
  },
  body: p => {
    const pads = []
    const leftY = [-14.77,-12.23,-9.69,-7.15,-4.61,-2.07,0.47,3.01,5.55,8.09,10.63,13.17]
    for (let i=0;i<12;i++) pads.push([i+2,-8.82,leftY[i],p['P'+(i+2)]])
    const rightNums = [30,29,28,27,26,25,24,23,22,21,20,19]
    for (let i=0;i<12;i++) pads.push([rightNums[i],6.42,leftY[i],p['P'+rightNums[i]]])
    pads.push([32,-6.275,10.63,p.P32])
    return `
      (module KLOR_HELIOS_REV1_HOST (layer F.Cu)
        ${p.at}
        (fp_text reference "${p.ref}" (at 0 -0.8) (layer F.SilkS) ${p.ref_hide}
          (effects (font (size 1 1) (thickness 0.15))))
        (fp_text value "0xCB Helios rev1.0" (at -1.2 15.8) (layer F.Fab) hide
          (effects (font (size 1 1) (thickness 0.15))))
        (fp_rect (start -10.4 -18.58) (end 8.0 14.75) (layer Dwgs.User) (width 0.15) (fill none))
        ${pads.map(([n,x,y,net]) => `(pad ${n} thru_hole ${n===2?'rect':'circle'} (at ${x} ${y} ${p.r}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) ${net || ''})`).join('\n')}
      )
    `
  }
}
