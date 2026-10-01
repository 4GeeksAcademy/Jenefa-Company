/** @type {import('next').NextConfig} */
const apiOrigin = process.env.HEALTHCORE_API_ORIGIN || "http://127.0.0.1:8000";

module.exports = {
	reactStrictMode: true,
	async rewrites() {
		return [
			{
				source: "/api/backend/:path*",
				destination: `${apiOrigin}/:path*`,
			},
		];
	},
};
