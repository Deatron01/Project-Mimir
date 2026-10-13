/**
 * Palette → mascot mapping. Every colour palette has its own mascot, and switching palettes switches the mascot.
 *
 * Artwork is picked up automatically from `src/assets/mascots/`, named after the palette id:
 *   forest.png             – the default pose for the "forest" palette
 *   forest-happy.png       – optional moods: happy | thinking | wave (fall back to the default pose)
 *   forest-face.png        – optional head crop, used at avatar sizes where a whole figure would be a few pixels wide
 * Any of .svg .png .webp .avif .gif .jpg works. Palettes without artwork show the built-in placeholder.
 */
import paletteData from './palettes.json';

export type MascotMood = 'idle' | 'happy' | 'thinking' | 'wave';
export const MASCOT_MOODS: MascotMood[] = ['idle', 'happy', 'thinking', 'wave'];
/** A file per mood, plus the head crop. */
export type MascotPose = MascotMood | 'face';
const MASCOT_POSES: MascotPose[] = [...MASCOT_MOODS, 'face'];
/** Below this size (px) the head crop is shown instead of the whole figure. */
export const MASCOT_FACE_BELOW = 56;

/** Accessory the placeholder mascot wears, so each palette is recognisable before the real artwork lands. */
export type MascotAccessory = 'cap' | 'moon' | 'sun' | 'flower' | 'leaf';

export interface MascotInfo {
  paletteId: string;
  accessory: MascotAccessory;
  /** Resolved image URLs by pose; empty until artwork is added. */
  art: Partial<Record<MascotPose, string>>;
}

const ACCESSORIES: Record<string, MascotAccessory> = {
  original: 'cap',
  midnight: 'moon',
  library: 'cap',
  sunset: 'sun',
  lavender: 'flower',
  forest: 'leaf',
};

const files = import.meta.glob('../assets/mascots/*.{svg,png,webp,avif,gif,jpg,jpeg}', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>;

/** Parses `…/mascots/<palette>[-<pose>].<ext>` into a palette → pose → url table. */
export function indexArt(paths: Record<string, string>): Record<string, Partial<Record<MascotPose, string>>> {
  const out: Record<string, Partial<Record<MascotPose, string>>> = {};
  for (const [path, url] of Object.entries(paths)) {
    const base = path.split('/').pop()!.replace(/\.[^.]+$/, '').toLowerCase();
    const dash = base.lastIndexOf('-');
    const maybePose = dash > 0 ? (base.slice(dash + 1) as MascotPose) : undefined;
    const [palette, pose] = maybePose && MASCOT_POSES.includes(maybePose) ? [base.slice(0, dash), maybePose] : [base, 'idle' as const];
    (out[palette] ??= {})[pose] = url;
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

/**
 * The image for a mood, falling back to the palette's default pose; undefined means "use the placeholder".
 * At avatar sizes the head crop wins when there is one, whatever the mood.
 */
export function mascotArt(info: MascotInfo, mood: MascotMood, size = MASCOT_FACE_BELOW): string | undefined {
  return (size < MASCOT_FACE_BELOW ? info.art.face : undefined) ?? info.art[mood] ?? info.art.idle;
}
