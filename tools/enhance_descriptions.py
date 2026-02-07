#!/usr/bin/env python3
"""Generate enhanced descriptions for rooms with short descriptions."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ZONES_DIR = BASE_DIR / 'world' / 'zones'

# Enhanced descriptions mapped by zone and vnum
DESCRIPTIONS = {
    # Zone 25: The High Tower Of Magic
    25: {
        2612: "Absolute darkness surrounds you in this sealed chamber. The air crackles with residual magical energy, and you sense ancient wards blocking all light from entering this sanctum.",
        2662: "Pitch black engulfs you completely. The tower's magical darkness is so profound that even enchanted lights fail to pierce it. You feel the weight of powerful spells maintaining this void.",
    },
    
    # Zone 31: Southern part of Midgaard
    31: {
        3110: "The cityguard headquarters buzzes with activity. Stone walls are lined with weapon racks and duty rosters. Guards in polished armor stand ready, while others study maps of patrol routes.",
        3118: "Cobblestones give way to smooth flagstones along this well-maintained park road. Ancient oak trees provide shade overhead, and the scent of flowers drifts from nearby gardens.",
        3124: "Elm Street ends here at a weathered stone wall marking the city's southern boundary. A single lantern flickers at the corner, casting long shadows across the quiet residential district.",
    },
    
    # Zone 36: The Chessboard of Midgaard - Alternating patterns based on color
    36: {
        3617: "You stand upon a gleaming white marble square. The polished stone reflects an ethereal glow, and the air shimmers with magical energy. Across the board, you can see towering chess pieces locked in eternal battle.",
        3618: "This black obsidian square absorbs the light around it. The dark stone feels cold beneath your feet, and shadows seem to pool at the edges. Giant chess pieces loom in the distance.",
        3619: "Pristine white marble stretches beneath you, almost blinding in its brightness. The square pulses with faint magical luminescence, part of the grand chessboard's enchantment.",
        3620: "Deep black stone forms this square, polished to a mirror-like finish. The obsidian feels unnaturally cold, and you can hear the distant grinding of massive chess pieces moving across the board.",
        3621: "This white square gleams like fresh snow under an invisible sun. Magical runes are etched along its edges, part of the ancient game's binding spell.",
        3622: "Jet-black obsidian forms this square, darker than night. The stone seems to whisper with ancient magic, and your footsteps echo strangely across its surface.",
        3623: "Brilliant white marble radiates a subtle warmth. This square sits at a strategic position on the mystical chessboard, and you sense powerful pieces have stood here.",
        3625: "Darkness pools on this black square, the obsidian drinking in all light. Faint energy pulses beneath your feet, part of the board's eternal enchantment.",
        3626: "Ivory-white stone gleams beneath you, immaculately smooth. The square feels charged with anticipation, as if waiting for the next move in an endless game.",
        3627: "This black square feels heavier than the others, as if weighted with importance. The obsidian is flawless, reflecting distorted images of the towering chess pieces.",
        3628: "Pure white marble forms this square, unblemished and bright. Magical energy crackles faintly at the edges where white meets black across the board.",
        3629: "Coal-black stone stretches beneath you, cold and unyielding. The square seems to absorb sound as well as light, creating an eerie pocket of silence.",
        3630: "This white square practically glows with inner light. The marble feels ancient beyond measure, worn smooth by centuries of magical combat above.",
        3633: "Gleaming white marble forms this square near the board's edge. The stone is cool to the touch, and you can sense the boundary of the magical playing field nearby.",
        3634: "Obsidian black as a moonless night forms this square. Strange reflections dance across its surface, showing glimpses of moves long past in this eternal game.",
        3635: "Brilliant white stone radiates subtle power. This square occupies a tactical position, and faint scorch marks suggest it's seen magical combat.",
        3636: "Deep black obsidian forms this square, its surface polished to perfection. The stone seems to hum with barely contained magical energy.",
        3637: "This white square shimmers with protective enchantments. The marble feels solid and reassuring, a bastion of light against the surrounding darkness.",
        3638: "Darkness incarnate forms this black square. The obsidian is so perfectly black it's difficult to gauge depth, creating a subtle sense of vertigo.",
        3639: "Pristine white marble stretches in a perfect square. Ancient runes carved into its edges glow faintly, maintaining the board's magical integrity.",
        3641: "This black square feels different from the others - colder, darker, more ominous. The obsidian seems to pull at you slightly, as if gravity is stronger here.",
        3642: "Radiant white marble forms this square, almost painful to look at in its brightness. The stone vibrates with barely perceptible magical energy.",
        3643: "Black as the void between stars, this obsidian square seems to exist slightly out of phase with reality. Your footsteps make no sound upon it.",
        3644: "This white square gleams like polished bone. The marble is ancient yet eternal, part of a game that transcends normal time and space.",
        3645: "Jet-black stone forms this square, its surface mirror-smooth. Dark reflections show distorted versions of yourself, twisted by the board's magic.",
        3646: "Pure white marble radiates a comforting warmth. This square feels safe, protected by the same magic that maintains the entire chessboard realm.",
        3647: "Obsidian darker than shadows forms this square. The black stone seems to swallow light and sound, creating a pocket of profound silence and darkness.",
        3648: "This white square marks the edge of the board. The marble transitions into nothingness beyond, where the magical playing field ends and reality resumes.",
    },
    
    # Zone 50: The Great Eastern Desert
    50: {
        5002: "The tunnel stretches endlessly through solid rock, carved by ancient hands or perhaps erosion from underground rivers. Limestone walls glisten with moisture, and your footsteps echo into the darkness ahead.",
        5003: "Rough-hewn stone walls press in from both sides as the tunnel continues its descent. The air grows cooler here, and you can hear the distant drip of water echoing through unseen chambers.",
        5004: "Multiple tunnels converge at this intersection, each passage disappearing into darkness. Strange symbols are carved into the junction's walls, possibly markers left by whoever built these passages.",
        5012: "The tunnel bends sharply here, forcing you to navigate carefully around jagged outcroppings. Water trickles down the curved wall, leaving mineral deposits that sparkle in any available light.",
        5015: "A natural underground pool fills this chamber, its surface perfectly still and dark as obsidian. The water looks deep and ancient, fed by underground springs that predate the desert above.",
    },
    
    # Zone 51: Drow City
    51: {
        5118: "The Warriors' Academy fills this vast cavern with the sounds of combat training. Drow fighters practice deadly techniques under the watchful eyes of weapon masters, their movements fluid and precise in the dim faerie fire light.",
    },
    
    # Zone 53: The Great Pyramid
    53: {
        5334: "Ancient stone blocks form the walls of this narrow tunnel, each carved with hieroglyphs that glow faintly in the darkness. The air is stale and heavy with the weight of millennia, and sand sifts down from hidden cracks above.",
    },
    
    # Zone 54: New Thalos
    54: {
        5457: "Beneath the streets of Thalos, this underground chamber serves some forgotten purpose. Water stains mark the stone walls, and debris litters the floor. Distant sounds of the city above echo faintly through cracks in the ceiling.",
        5459: "This narrow alley cuts between two towering buildings, barely wide enough for a cart to pass. Shadows gather in the cramped space, and the smell of refuse and cooking fires mingles unpleasantly.",
        5476: "The underground passage is dark and damp, with moisture seeping through ancient mortar. Stone pillars support the ceiling, and you can hear the muffled sounds of the marketplace directly above you.",
        5492: "Beneath Thalos, this subterranean room shows signs of old construction - perhaps part of the original city before it was built over. Crumbling brick walls and a low ceiling create a claustrophobic atmosphere.",
        5493: "The underground chamber extends into darkness, its original purpose long forgotten. Stone blocks form the walls, and rubble is piled in corners. Somewhere ahead, you hear the echo of dripping water.",
        5500: "This hidden space beneath the city streets was clearly once more grand. Now water seeps through cracks, and the stone floor is uneven from settling. Rats scurry in the shadows between fallen stonework.",
        5501: "Deep underground, this chamber smells of damp earth and decay. The walls are rough-cut stone, and wooden beams shore up sections of ceiling that look ready to collapse.",
        5502: "The underground room is cramped and dark, with barely enough headroom to stand. Water has pooled in low spots on the uneven floor, and the air is thick with moisture and the smell of mold.",
        5616: "The road here is well-maintained, paved with fitted stones worn smooth by countless travelers. Buildings line both sides, and you can hear the bustle of Thalos's commerce and daily life all around you.",
        5621: "The River Ishtar flows swiftly here, its waters dark and deep. Stone embankments channel the current through the city, and you can see bridges spanning the river both upstream and downstream.",
        5630: "Paved stones form this section of road through Thalos. Buildings of varying heights line the way, their architecture showing the city's long history. Merchants and citizens go about their business around you.",
        5631: "The road continues through the city, well-traveled and maintained. Stone buildings rise on either side, some showing their age, others more recently constructed or renovated. The sounds of urban life surround you.",
        5632: "This stretch of road sees heavy foot traffic through Thalos. The paving stones are worn smooth in the center where most people walk, while the edges show the original chisel marks from when they were laid.",
        5648: "The mighty River Ishtar dominates this view, its waters flowing powerfully through the heart of Thalos. The riverbank is reinforced with fitted stones, and you can see boats and barges plying the current.",
    },
    
    # Zone 65: The Dwarven Kingdom
    65: {
        6528: "Stone stairs spiral upward through Castle Strangelove's interior. The steps are worn smooth by countless boots over the years, and arrow slits in the thick walls provide narrow views of the surrounding kingdom.",
        6548: "The maze twists and turns through carved stone passages. Each corridor looks identical to the last, deliberately designed to confuse intruders. The air is cool and still, and sound travels strangely through the labyrinth.",
        6549: "Identical stone walls press in from all sides in this section of the maze. The passages split and rejoin in bewildering patterns, and you've lost all sense of direction in this dwarven-crafted puzzle.",
        6550: "The maze continues its disorienting pattern of stone corridors and dead ends. Every wall looks the same, every turn potentially leading you deeper into the labyrinth or back to where you started.",
    },
    
    # Zone 72: The Sewer Maze
    72: {
        7220: "This drain connects to the larger sewer system, exactly as mundane as you'd expect. Slime coats the curved walls, and the constant trickle of questionable fluids echoes in the confined space.",
        7340: "The southwestern corner of the basilisk's massive cave lair stretches before you. Ancient stone bears deep claw marks, and the air reeks of reptile musk. Bones crunch underfoot - remains of previous victims.",
    },
    
    # Zone 79: Redferne's Residence
    79: {
        7908: "The wizard's enchanted fridge hums with magical energy, maintaining a temperature far below freezing without any visible mechanism. Frost covers the interior walls, and preserved specimens float in stasis within crystalline containers.",
    },
}

def enhance_zones():
    """Apply enhanced descriptions to zones."""
    updated_count = 0
    
    for zone_num, descriptions in DESCRIPTIONS.items():
        zone_file = ZONES_DIR / f"zone_{zone_num:03d}.json"
        
        if not zone_file.exists():
            print(f"⚠️  Zone file not found: {zone_file}")
            continue
        
        # Load zone
        with open(zone_file, 'r') as f:
            zone_data = json.load(f)
        
        zone_name = zone_data.get('name', 'Unknown')
        print(f"\n📦 Updating Zone {zone_num}: {zone_name}")
        
        # Update rooms
        for vnum, new_desc in descriptions.items():
            vnum_str = str(vnum)
            if vnum_str in zone_data.get('rooms', {}):
                old_desc = zone_data['rooms'][vnum_str].get('description', '')
                zone_data['rooms'][vnum_str]['description'] = new_desc
                updated_count += 1
                print(f"   ✓ Room {vnum}: {zone_data['rooms'][vnum_str]['name']}")
                print(f"     Old ({len(old_desc)} chars): {old_desc[:50]}...")
                print(f"     New ({len(new_desc)} chars): {new_desc[:80]}...")
            else:
                print(f"   ⚠️  Room {vnum} not found in zone file")
        
        # Save updated zone
        with open(zone_file, 'w') as f:
            json.dump(zone_data, f, indent=2)
        
        print(f"   💾 Saved {zone_file.name}")
    
    print(f"\n{'='*80}")
    print(f"✅ Enhanced {updated_count} room descriptions across {len(DESCRIPTIONS)} zones")
    print(f"{'='*80}")

if __name__ == '__main__':
    enhance_zones()
