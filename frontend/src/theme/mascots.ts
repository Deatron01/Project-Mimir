/**
 * Palette → mascot mapping. Every colour palette has its own mascot, and switching palettes switches the mascot.
 *
 * Artwork is picked up automatically from `src/assets/mascots/`, named after the palette id:
 *   ocean.png              – the default pose for the "ocean" palette
 *   ocean-happy.png        – optional moods: happy | thinking | wave (fall back to the default pose)
 * Any of .svg .png .webp .avif .gif .jpg works. Palettes without artwork show the built-in placeholder.
 */
import paletteData from './palettes.json';

export type MascotMood = 'idle' | 'happy' | 'thinking' | 'wave';
export const MASCOT_MOODS: MascotMood[] = ['idle', 'happy', 'thinking', 'wave'];

/** Accessory the placeholder mascot wears, so each palette is recognisable before the real artwork lands. */
export type MascotAccessory = 'cap' | 'moon' | 'bubbles' | 'sun' | 'flower' | 'leaf';

export interface MascotInfo {
  paletteId: string;
  accessory: MascotAccessory;
  /** Resolved image URLs by mood; empty until artwork is added. */
  art: Partial<Record<MascotMood, string>>;
}

const ACCESSORIES: Record<string, MascotAccessory> = {
  original: 'cap',
  midnight: 'moon',
  ocean: 'bubbles',
  sunset: 'sun',
  lavender: 'flower',
  forest: 'leaf',
};

const files = import.meta.glob('../assets/mascots/*.{svg,png,webp,avif,gif,jpg,jpeg}', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>;

/** Parses `…/mascots/<palette>[-<mood>].<ext>` into a palette → mood → url table. */
export function indexArt(paths: Record<string, string>): Record<string, Partial<Record<MascotMood, string>>> {
  const out: Record<string, Partial<Record<MascotMood, string>>> = {};
  for (const [path, url] of Object.entries(paths)) {
    const base = path.split('/').pop()!.replace(/\.[^.]+$/, '').toLowerCase();
    const dash = base.lastIndexOf('-');
    const maybeMood = dash > 0 ? (base.slice(dash + 1) as MascotMood) : undefined;
    const [palette, mood] = maybeMood && MASCOT_MOODS.includes(maybeMood) ? [base.slice(0, dash), maybeMood] : [base, 'idle' as const];
    (out[palette] ??= {})[mood] = url;
  }
  return out;
}

const art = indexArt(files);

export const mascots: Record<string, MascotInfo> = Object.fromEntries(
  paletteData.palettes.map((p) => [p.id, { paletteId: p.id, accessory: ACCESSORIES[p.id] ?? 'cap', art: art[p.id] ?? {} }]),
);

export function getMascot(paletteId: string): MascotInfo {
  return mascots[paletteId] ?? mascots[paletteData.default.palette];
}

/** The image for a mood, falling back to the palette's default pose; undefined means "use the placeholder". */
export function mascotArt(info: MascotInfo, mood: MascotMood): string | undefined {
  return info.art[mood] ?? info.art.idle;
}
