/** @type {import('tailwindcss').Config} */
module.exports = {
	content: [
		"./public/**/*.html",
		"./www/**/*.html",
		"./templates/**/*.html",
		"./pitstop_email_digest/**/page/**/*.js",
		"./pitstop_email_digest/public/js/**/*.vue",
	],
	// Scope utilities to `.tw-scope` so they never clash with Frappe/Bootstrap desk styles
	important: ".tw-scope",
	corePlugins: {
		preflight: false,
		container: false,
	},
	theme: {
		extend: {},
	},
	plugins: [],
};
