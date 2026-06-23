/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: 'https://www.kritikaal.com',
  generateRobotsTxt: true,
  outDir: './out',
  changefreq: 'weekly',
  priority: 0.7,
  exclude: ['/admin/*', '/api/*'],
  robotsTxtOptions: {
    policies: [
      { userAgent: '*', allow: '/' },
      { userAgent: 'GPTBot', allow: '/' },
      { userAgent: 'ClaudeBot', allow: '/' },
      { userAgent: 'PerplexityBot', allow: '/' },
      { userAgent: 'Googlebot', allow: '/' },
    ],
  },
};
