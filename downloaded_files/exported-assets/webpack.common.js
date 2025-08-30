const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { merge } = require('webpack-merge');

const commonConfig = {
  entry: './src/frontend/app.js',
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/frontend/index.html',
      title: 'FortiGate Topology Clone'
    })
  ],
  resolve: {
    extensions: ['.js', '.json'],
    alias: {
      '@': path.resolve(__dirname, 'src/frontend'),
      '@components': path.resolve(__dirname, 'src/frontend/components'),
      '@services': path.resolve(__dirname, 'src/frontend/services'),
      '@utils': path.resolve(__dirname, 'src/frontend/utils'),
      '@styles': path.resolve(__dirname, 'src/frontend/styles')
    }
  }
};

module.exports = commonConfig;