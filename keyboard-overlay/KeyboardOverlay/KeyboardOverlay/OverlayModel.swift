//
//  OverlayModel.swift
//  KeyboardOverlay
//
//  Created by Feiyang Fan on 2026-08-18.
//

import Foundation

struct KeyDisplay: Identifiable {
    let id: Int
    let label: String

    let x: CGFloat
    let y: CGFloat
    let width: CGFloat
    let height: CGFloat
    let rotation: Double
}
