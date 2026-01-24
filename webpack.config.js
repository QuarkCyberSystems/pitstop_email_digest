// webpack.config.js
const path = require("path");

module.exports = {
	// ... other configurations ...
	module: {
		rules: [
			{
				test: /\.css$/i,
				use: ["style-loader", "css-loader", "postcss-loader"],
			},
		],
	},
};
