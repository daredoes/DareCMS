var webpack = require('webpack');
var path = require('path');

var BUILD_DIR = path.resolve(__dirname, './hub/static/js');
var APP_DIR = path.resolve(__dirname, './hub/static/jsx');

var config = {
    entry: APP_DIR + '/index.jsx',
    output: {
        filename: 'bundle.js',
        path: BUILD_DIR
    },
    module: {
        loaders: [
            {
              test: /\.jsx?/,
              exclude: /(node_modules|bower_components)/,
              loader: 'babel-loader'
            }
        ]
    },
    plugins: [
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            "window.jQuery": "jquery"
        }),
        new webpack.ProvidePlugin({
            "React": "react",
            "ReactDOM": "react-dom"
          })
    ]
};

module.exports = config;

