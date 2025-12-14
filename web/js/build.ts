const esbuild = require('esbuild')
const tsPaths = require("esbuild-ts-paths")
const fs = require('fs')
const { execSync, spawn } = require('child_process')

const args = process.argv.slice(2)
const watch = args.includes('--watch')

async function build() {
  if (watch) {
    // For watch: Run tsc --watch --noEmit in background (logs errors but doesn't fail)
    console.log('Starting type checking in watch mode...');
    const tscProcess = spawn('npx', ['tsc', '--watch', '--noEmit']);
    tscProcess.stdout.on('data', (data: any) => console.log(data.toString().trim()));
    tscProcess.stderr.on('data', (data: any) => console.error(data.toString().trim()));
    tscProcess.on('error', (error: any) => console.error('Type checker failed to start:', error));
    // Note: This process will exit when the main script exits (e.g., Ctrl+C)
  } else {
    // For non-watch: Run tsc --noEmit sync and fail build on errors
    try {
      console.log('Checking types...');
      execSync('npx tsc --noEmit', { stdio: 'inherit' });  // Inherit stdio to log directly
      console.log('Types OK');
    } catch (error) {
      console.error('Type checking failed—aborting build');
      process.exit(1);
    }
  }

  const baseConfigJS = {
    entryPoints: ['index.tsx'],
    outfile: '../../static/app.js',
    bundle: true,
    minify: true,
    sourcemap: true,
    plugins: [
      tsPaths('./tsconfig.json')
    ].filter(Boolean)
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
