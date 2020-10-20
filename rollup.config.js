import postcss from 'rollup-plugin-postcss'
import copy from 'rollup-plugin-copy'
import commonjs from '@rollup/plugin-commonjs'
import resolve from '@rollup/plugin-node-resolve';

export default [
    {
        input: 'assets/css/style.scss',
        output: {
            file: 'public/assets/css/style.css',
        },
        plugins: [
            postcss({extract: true}),
            copy({
                targets: [
                    {src: 'assets/images/*', dest: 'public/assets/images/'},
                ]
            }),
        ]
    }, {
        input: 'assets/js/stats.js',
        output: {
            file: 'public/assets/js/stats.js',
            format: 'iife'
        },
        plugins: [
            resolve(),
            commonjs(),
            postcss(),
        ]
    }, {
        input: 'assets/js/recommz.js',
        output: {
            file: 'public/assets/js/recommz.js'
        },
        plugins: [
            postcss()
        ]
    }
];