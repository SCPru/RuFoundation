import * as esbuild from 'esbuild';
import {sassPlugin} from 'esbuild-sass-plugin';

const args = process.argv.slice(2);
const watch = args.includes('--watch');

async function build() {
    const baseConfigJS = {
        entryPoints: ['index.tsx'],
        outfile: '../../static/system.js',
        bundle: true,
        minify: true,
        sourcemap: true
    };

    const baseConfigCSS = {
        entryPoints: ['index.scss'],
        outfile: '../../static/system.css',
        bundle: true,
        minify: true,
        sourcemap: true,
        plugins: [sassPlugin()]
    };

    if (watch) {
        const createWatchLogger = (type: string) => ({
            onRebuild(error: any, result: any) {
                if (error) console.log(`Rebuild failed for ${type}`, error);
                else console.log(`Rebuild succeeded for ${type}`, result);
            }
        });

        esbuild.build(Object.assign(baseConfigJS, { watch: createWatchLogger('JS'), minify: false }));
        esbuild.build(Object.assign(baseConfigCSS, { watch: createWatchLogger('CSS'), minify: false }));
    } else {
        console.log('Building JS...');
        await esbuild.build(baseConfigJS);
        console.log('Building CSS...');
        await esbuild.build(baseConfigCSS);
    }
}

build();
