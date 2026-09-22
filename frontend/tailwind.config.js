/** @type {import('tailwindcss').Config} */
// Colours are CSS variables holding "R G B" channels (see src/theme/themes.css),
// so Tailwind opacity modifiers such as `bg-primary/20` work for every palette and mode.
const token = (name) => `rgb(var(--c-${name}) / <alpha-value>)`;

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: token('bg'),
        surface: token('surface'),
        border: token('border'),
        textMain: token('text'),
        muted: token('muted'),
        primary: token('primary'),
        onPrimary: token('on-primary'),
        accent: token('accent'),
        brandPrimary: token('brand-primary'),
        brandAccent: token('brand-accent'),
        danger: token('danger'),
        success: token('success'),
        warning: token('warning'),
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgb(0 0 0 / 0.37)',
      },
    },
  },
  plugins: [],
};
