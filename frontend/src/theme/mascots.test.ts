import { describe, expect, it } from 'vitest';
import { MASCOT_FACE_BELOW, getMascot, indexArt, mascotArt, mascots } from './mascots';
import paletteData from './palettes.json';
import { initials } from '../components/topics/ClassAvatar';

describe('mascots', () => {
  it('has a mascot for every palette', () => {
    for (const p of paletteData.palettes) expect(mascots[p.id]?.paletteId).toBe(p.id);
  });

  it('indexes artwork by palette and pose from the file name', () => {
    const art = indexArt({
      '../assets/mascots/forest.png': '/a/forest.png',
      '../assets/mascots/forest-happy.webp': '/a/forest-happy.webp',
      '../assets/mascots/forest-face.webp': '/a/forest-face.webp',
      '../assets/mascots/Sunset-Wave.SVG': '/a/sunset-wave.svg',
      '../assets/mascots/sunset-glow.png': '/a/sunset-glow.png',
    });
    expect(art.forest).toEqual({ idle: '/a/forest.png', happy: '/a/forest-happy.webp', face: '/a/forest-face.webp' });
    expect(art.sunset).toEqual({ wave: '/a/sunset-wave.svg' });
    // An unknown suffix is part of the palette id, not a pose.
    expect(art['sunset-glow']).toEqual({ idle: '/a/sunset-glow.png' });
  });

  it('uses the head crop at avatar sizes only', () => {
    const info = { paletteId: 'x', accessory: 'cap' as const, art: { idle: '/idle.png', wave: '/wave.png', face: '/face.png' } };
    expect(mascotArt(info, 'wave', MASCOT_FACE_BELOW - 1)).toBe('/face.png');
    expect(mascotArt(info, 'wave', MASCOT_FACE_BELOW)).toBe('/wave.png');
    expect(mascotArt(info, 'wave')).toBe('/wave.png');
    expect(mascotArt({ ...info, art: { idle: '/idle.png' } }, 'wave', 20)).toBe('/idle.png');
  });

  it('ships a figure and a head crop for every palette', () => {
    for (const p of paletteData.palettes) {
      expect(mascots[p.id].art.idle, p.id).toBeTruthy();
      expect(mascots[p.id].art.face, p.id).toBeTruthy();
    }
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
