import postcss from 'rollup-plugin-postcss'
import copy from 'rollup-plugin-copy'
import commonjs from '@rollup/plugin-commonjs'
import resolve from '@rollup/plugin-node-resolve';
import babel from '@rollup/plugin-babel';

const config_css = [
    {
        input: 'assets/css/style.scss',
        output: {
            dir: 'public/assets/css/',
            entryFileNames: '[name].css'
        },
        plugins: [
            postcss({extract: true}),
            copy({
                targets: [
                    {src: 'assets/images/*', dest: 'public/assets/images/'},
                ]
            }),
        ]
    }
];

const config_js = ['assets/js/recommz.js', 'assets/js/stats.js'].map(
    filename => {
        return {
            input: filename,
            output: {
                entryFileNames: '[name].js',
                dir: 'public/assets/js/',
                sourcemap: true,
                format: 'iife',
            },
            plugins: [
                commonjs(),
                postcss(),
                babel({
                    babelHelpers: 'bundled',
                    exclude: 'node_modules/**'
                }),
                resolve(),
            ],

        }
    }
)
export default config_css.concat(config_js)