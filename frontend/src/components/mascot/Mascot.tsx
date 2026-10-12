import { AnimatePresence, motion } from 'framer-motion';
import { useTheme } from '../../context/ThemeContext';
import { getMascot, mascotArt, type MascotAccessory, type MascotMood } from '../../theme/mascots';
import { cn } from '../../utils/cn';
import paletteData from '../../theme/palettes.json';

interface Props {
  mood?: MascotMood;
  size?: number;
  /** Speech bubble text. Real text, read by screen readers; the mascot itself is decorative. */
  say?: React.ReactNode;
  bubbleSide?: 'right' | 'top';
  /** Gentle idle bobbing. Disabled automatically for "reduce motion". */
  float?: boolean;
  className?: string;
  /** Override the palette (e.g. previews in the palette picker). */
  paletteId?: string;
}

/**
 * The palette's mascot. Switching palette swaps it with a little pop, Duolingo style.
 * Uses the artwork from src/assets/mascots when present, otherwise a placeholder drawn in the palette's colours.
 */
export default function Mascot({ mood = 'idle', size = 96, say, bubbleSide = 'right', float = true, className, paletteId }: Props) {
  const theme = useTheme();
  const id = paletteId ?? theme.paletteId;
  const info = getMascot(id);
  const src = mascotArt(info, mood);

  const figure = (
    <div className="relative shrink-0" style={{ width: size, height: size, ...(paletteId ? paletteVars(paletteId) : undefined) }} aria-hidden="true">
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.div
          key={`${id}-${mood}`}
          className="absolute inset-0"
          initial={{ scale: 0.4, rotate: -12, opacity: 0 }}
          animate={{ scale: 1, rotate: 0, opacity: 1 }}
          exit={{ scale: 0.4, rotate: 12, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 420, damping: 22 }}
        >
          <motion.div
            className="h-full w-full"
            animate={float ? { y: [0, -size * 0.04, 0] } : undefined}
            transition={float ? { duration: 3.2, repeat: Infinity, ease: 'easeInOut' } : undefined}
          >
            {src ? (
              <img src={src} alt="" className="h-full w-full object-contain" draggable={false} />
            ) : (
              <PlaceholderMascot mood={mood} accessory={info.accessory} />
            )}
          </motion.div>
        </motion.div>
      </AnimatePresence>
    </div>
  );

  if (!say) return <div className={cn('inline-flex', className)}>{figure}</div>;

  return (
    <div className={cn('flex items-end gap-3', bubbleSide === 'top' && 'flex-col-reverse items-center', className)}>
      {figure}
      <motion.div
        key={typeof say === 'string' ? say : undefined}
        initial={{ opacity: 0, scale: 0.9, y: 6 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className={cn(
          'relative max-w-xs rounded-2xl border border-border/50 bg-surface px-4 py-3 text-sm font-medium leading-snug text-textMain shadow-sm',
          bubbleSide === 'right' ? 'mb-[18%] rounded-bl-md' : 'rounded-b-2xl',
        )}
      >
        {say}
      </motion.div>
    </div>
  );
}

const channels = (hex: string) => {
  const n = parseInt(hex.replace('#', ''), 16);
  return `${(n >> 16) & 255} ${(n >> 8) & 255} ${n & 255}`;
};

/** Brand colours of another palette as scoped CSS variables, so a preview mascot wears its own palette. */
function paletteVars(id: string): React.CSSProperties | undefined {
  const p = paletteData.palettes.find((x) => x.id === id);
  if (!p) return undefined;
  return { '--c-brand-primary': channels(p.dark.brandPrimary), '--c-brand-accent': channels(p.dark.brandAccent) } as React.CSSProperties;
}

const C = {
  body: 'rgb(var(--c-brand-primary))',
  belly: 'rgb(var(--c-brand-accent))',
  accent: 'rgb(var(--c-brand-accent))',
  dark: '#1d2430',
  warm: '#f6b84b',
};

/** Simple owl ("Mímir's wisdom") in the palette's brand colours; replaced by real artwork per palette. */
function PlaceholderMascot({ mood, accessory }: { mood: MascotMood; accessory: MascotAccessory }) {
  const happy = mood === 'happy';
  const thinking = mood === 'thinking';
  const wave = mood === 'wave';
  return (
    <svg viewBox="0 0 120 120" className="h-full w-full overflow-visible" role="presentation">
      {accessory === 'sun' && (
        <g>
          <circle cx="92" cy="26" r="13" fill={C.warm} opacity="0.9" />
          {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => (
            <rect key={a} x="91" y="5" width="2.5" height="6" rx="1.2" fill={C.warm} transform={`rotate(${a} 92 26)`} />
          ))}
        </g>
      )}
      {accessory === 'moon' && (
        <g fill="#f5e9b8">
          <path d="M96 10a14 14 0 1 0 12 22 11 11 0 1 1-12-22z" />
          <circle cx="22" cy="18" r="1.8" />
          <circle cx="12" cy="34" r="1.2" />
          <circle cx="108" cy="50" r="1.4" />
        </g>
      )}
      {accessory === 'bubbles' && (
        <g fill="none" stroke={C.accent} strokeWidth="2" opacity="0.9">
          <circle cx="98" cy="22" r="6" />
          <circle cx="108" cy="38" r="3.5" />
          <circle cx="16" cy="30" r="4" />
        </g>
      )}

      {/* shadow */}
      <ellipse cx="60" cy="113" rx="30" ry="4" fill="currentColor" opacity="0.12" />
      {/* ear tufts */}
      <path d="M30 36 L26 14 L46 28 Z" fill={C.body} />
      <path d="M90 36 L94 14 L74 28 Z" fill={C.body} />
      {/* body */}
      <ellipse cx="60" cy="66" rx="36" ry="42" fill={C.body} />
      <ellipse cx="60" cy="78" rx="23" ry="26" fill={C.belly} opacity="0.55" />
      {/* belly feathers */}
      <g fill="none" stroke={C.body} strokeWidth="2" strokeLinecap="round" opacity="0.7">
        <path d="M50 74q4 4 8 0" />
        <path d="M62 74q4 4 8 0" />
        <path d="M56 84q4 4 8 0" />
      </g>
      {/* wings */}
      <path d="M25 62 q-8 18 6 34 q6-14 2-34z" fill={C.body} stroke={C.dark} strokeOpacity="0.15" />
      <g transform={wave ? 'rotate(-55 93 60)' : thinking ? 'rotate(-25 93 60)' : undefined}>
        <path d="M95 62 q8 18 -6 34 q-6-14 -2-34z" fill={C.body} stroke={C.dark} strokeOpacity="0.15" />
      </g>
      {/* eyes */}
      <circle cx="45" cy="50" r="13" fill="#fff" />
      <circle cx="75" cy="50" r="13" fill="#fff" />
      {happy ? (
        <g fill="none" stroke={C.dark} strokeWidth="3.5" strokeLinecap="round">
          <path d="M38 52q7-8 14 0" />
          <path d="M68 52q7-8 14 0" />
        </g>
      ) : (
        <g fill={C.dark}>
          <circle cx={thinking ? 48 : 46} cy={thinking ? 46 : 51} r="6" />
          <circle cx={thinking ? 78 : 76} cy={thinking ? 46 : 51} r="6" />
          <circle cx={thinking ? 50 : 48} cy={thinking ? 44 : 49} r="2" fill="#fff" />
          <circle cx={thinking ? 80 : 78} cy={thinking ? 44 : 49} r="2" fill="#fff" />
        </g>
      )}
      {/* beak */}
      <path d="M55 60 L65 60 L60 69 Z" fill={C.warm} />
      {happy && (
        <g fill="#f08a8a" opacity="0.55">
          <ellipse cx="34" cy="63" rx="5" ry="3" />
          <ellipse cx="86" cy="63" rx="5" ry="3" />
        </g>
      )}
      {thinking && <circle cx="100" cy="30" r="3" fill={C.accent} opacity="0.8" />}
      {/* feet */}
      <g fill={C.warm}>
        <ellipse cx="48" cy="107" rx="7" ry="3.5" />
        <ellipse cx="72" cy="107" rx="7" ry="3.5" />
      </g>

      {accessory === 'cap' && (
        <g>
          <path d="M34 26 L60 15 L86 26 L60 36 Z" fill={C.dark} />
          <path d="M44 30 v8 q16 8 32 0 v-8 L60 36 Z" fill={C.dark} opacity="0.9" />
          <path d="M84 27 v13" stroke={C.warm} strokeWidth="2" />
          <circle cx="84" cy="41" r="2.5" fill={C.warm} />
        </g>
      )}
      {accessory === 'flower' && (
        <g transform="translate(76 22)">
          {[0, 72, 144, 216, 288].map((a) => (
            <ellipse key={a} cx="0" cy="-7" rx="4.5" ry="7" fill={C.accent} transform={`rotate(${a})`} />
          ))}
          <circle r="4" fill={C.warm} />
        </g>
      )}
      {accessory === 'leaf' && (
        <g transform="translate(60 18) rotate(-20)">
          <path d="M0 0 q14 -16 0 -30 q-14 14 0 30z" fill="#5fae6b" />
          <path d="M0 0 v-26" stroke="#2f6b3a" strokeWidth="1.5" />
        </g>
      )}
    </svg>
  );
}
