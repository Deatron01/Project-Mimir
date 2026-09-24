import type { StorybookConfig } from '@storybook/react-vite';

// FE-UX-04: component catalogue with palette × mode × language switches and an accessibility panel.
const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(ts|tsx)'],
  addons: ['@storybook/addon-a11y'],
  framework: { name: '@storybook/react-vite', options: {} },
  staticDirs: ['../public'],
};
export default config;
