import { describe, expect, it } from 'vitest';
import { getMascot, indexArt, mascotArt, mascots } from './mascots';
import paletteData from './palettes.json';
import { initials } from '../components/topics/ClassAvatar';

describe('mascots', () => {
  it('has a mascot for every palette', () => {
    for (const p of paletteData.palettes) expect(mascots[p.id]?.paletteId).toBe(p.id);
  });

  it('indexes artwork by palette and mood from the file name', () => {
    const art = indexArt({
      '../assets/mascots/ocean.png': '/a/ocean.png',
      '../assets/mascots/ocean-happy.webp': '/a/ocean-happy.webp',
      '../assets/mascots/Forest-Wave.SVG': '/a/forest-wave.svg',
      '../assets/mascots/sunset-glow.png': '/a/sunset-glow.png',
    });
    expect(art.ocean).toEqual({ idle: '/a/ocean.png', happy: '/a/ocean-happy.webp' });
    expect(art.forest).toEqual({ wave: '/a/forest-wave.svg' });
    // An unknown suffix is part of the palette id, not a mood.
    expect(art['sunset-glow']).toEqual({ idle: '/a/sunset-glow.png' });
  });

  it('falls back to the default pose, then to the placeholder', () => {
    const info = { paletteId: 'x', accessory: 'cap' as const, art: { idle: '/idle.png' } };
    expect(mascotArt(info, 'happy')).toBe('/idle.png');
    expect(mascotArt({ ...info, art: {} }, 'happy')).toBeUndefined();
    expect(getMascot('does-not-exist').paletteId).toBe(paletteData.default.palette);
  });
});

describe('class initials', () => {
  it('uses up to two letters or digits', () => {
    expect(initials('Math')).toBe('M');
    expect(initials('Fotoszintézis (demo)')).toBe('FD');
    expect(initials('biology 9 – cells')).toBe('B9');
    expect(initials('  (( ')).toBe('?');
  });
});
