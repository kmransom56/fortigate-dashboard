/** @type {import('tailwindcss').Config} */

export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				primary: {
					50: '#f0f9ff',
					500: '#0ea5e9',
					600: '#0284c7',
					700: '#0369a1',
					900: '#0c4a6e'
				},
				gray: {
					800: '#1f2937',
					900: '#111827'
				},
				success: '#10b981',
				warning: '#f59e0b',
				error: '#ef4444'
			},
			fontFamily: {
				mono: ['Monaco', 'Consolas', 'Liberation Mono', 'monospace']
			}
		}
	},
	plugins: [require('@tailwindcss/forms')]
};
