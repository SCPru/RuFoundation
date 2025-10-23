const esbuild = require('esbuild')
const tsPaths = require("esbuild-ts-paths")
const fs = require('fs');

const args = process.argv.slice(2)
const watch = args.includes('--watch')

async function build() {
  const baseConfigJS = {
    entryPoints: ['index.tsx'],
    outfile: '../../static/app.js',
    bundle: true,
    minify: true,
    sourcemap: true,
    plugins: [tsPaths('./tsconfig.json')]
  }

  if (watch) {
    const createWatchLogger = (type: string) => ({
      onRebuild(error: any, result: any) {
        if (error) console.log(`Rebuild failed for ${type}`, error)
        else console.log(`Rebuild succeeded for ${type}`, result)
      },
    })

    esbuild.build(Object.assign(baseConfigJS, { watch: createWatchLogger('JS'), minify: false }))
  } else {
    console.log('Building JS...')
    await esbuild.build(baseConfigJS)
    console.log('Building CSS...')
  }
}

fs.copyFileSync('./node_modules/highlight.js/styles/github.css', '../../static/highlight.js.css');

build()
